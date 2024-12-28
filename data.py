from nba_api.stats.endpoints import playercareerstats, teamyearbyyearstats
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import players, teams
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

def get_live_data():
    sb = scoreboard.ScoreBoard().games.get_dict()
    live_games = []
    is_live = False
    for game in sb:
        live_games.append({
            "gameID" :  game["gameId"],
            "gameStatusText" : game["gameStatusText"],
            "period" : game["period"],
            "homeTeam" : {
                "teamID" : game["homeTeam"]["teamId"],
                "teamName" : game["homeTeam"]["teamName"],
                "wins": game["homeTeam"]["wins"],
                "losses" : game["homeTeam"]["losses"],
                "score" : game["homeTeam"]["score"],
            },
            "awayTeam" : {
                "teamID" : game["awayTeam"]["teamId"],
                "teamName" : game["awayTeam"]["teamName"],
                "wins": game["awayTeam"]["wins"],
                "losses" : game["awayTeam"]["losses"],
                "score" : game["awayTeam"]["score"],
            },
        })
        period = []
        for i in range(0, game["period"]):
            period.append(
                "{}-{}".format(game["homeTeam"]["periods"][i]["score"], game["awayTeam"]["periods"][i]["score"])
            )
        live_games[-1]["periods"] = period
        if live_games[-1]["period"] != "":
            is_live = True
    live_games[-1] = is_live
    return live_games

def get_data(type, id):
    settings = {}
    if type == "team":
        settings["data"] = teamyearbyyearstats.TeamYearByYearStats(team_id=id)
        settings["name"] = teams.find_team_name_by_id(id)
        settings["final_stats"] = settings["data"].get_normalized_dict()["TeamStats"]
        settings["size"] = len(settings["final_stats"])-35
        settings["year_type"] = "YEAR"
    
    elif type == "player":
        settings["data"] = playercareerstats.PlayerCareerStats(player_id=id)
        settings["name"] = players.find_player_by_id(id)
        settings["final_stats"] = settings["data"].get_normalized_dict()["SeasonTotalsRegularSeason"]
        settings["size"] = 0
        settings["year_type"] = "SEASON_ID"
            
    data = settings["data"]
    size = settings["size"]
    finStats = settings["final_stats"]
    
    labels = []
    pts = []
    rebs = []
    asts = []
    stls = []
    blks = []
    effs = []
    
    for i in range(size, len(finStats)):
        if len(labels) != 0 and finStats[i][settings["year_type"]] == labels[-1]:
            pts[-1] += finStats[i]["PTS"]
            rebs[-1] += finStats[i]["REB"]
            asts[-1] += finStats[i]["AST"]
            stls[-1] += finStats[i]["STL"]
            blks[-1] += finStats[i]["BLK"]
            efficiency = (finStats[i]["PTS"] + finStats[i]["REB"] + finStats[i]["AST"] + finStats[i]["STL"] + finStats[i]["BLK"]
                        - (finStats[i]["FGA"] - finStats[i]["FGM"]) - (finStats[i]["FTA"] - finStats[i]["FTM"]) - finStats[i]["TOV"]) / finStats[i]["GP"]
            effs[-1] = round((effs[-1] + efficiency) / 2)
        else:
            labels.append(finStats[i][settings["year_type"]])
            pts.append(finStats[i]["PTS"])
            rebs.append(finStats[i]["REB"])
            asts.append(finStats[i]["AST"])
            stls.append(finStats[i]["STL"])
            blks.append(finStats[i]["BLK"])
            efficiency = (pts[-1] + rebs[-1] + asts[-1] + stls[-1] + blks[-1]
                        - (finStats[i]["FGA"] - finStats[i]["FGM"]) - (finStats[i]["FTA"] - finStats[i]["FTM"]) - finStats[i]["TOV"]) / finStats[i]["GP"]
            effs.append(efficiency)
    
    finStatsDict = {"PTS": pts, "REB": rebs, "AST": asts,
                    "STL": stls, "BLK": blks, "EFF": effs, "NAME": settings["name"]["full_name"], "LABELS": labels}
    
    statsDict = {"data": finStatsDict}
    return statsDict


class SimpleRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        
        raw_body = self.rfile.read(content_length)
        
        try:
            body_data = json.loads(raw_body.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_response(400)
        
        if (body_data["type"] == "live"):
            body_data = get_live_data()
        else:
            body_data = get_data(body_data["type"], body_data["id"])
        
        response_data = {"status": "OK", "received": body_data}
        response_bytes = json.dumps(response_data).encode('utf-8')

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response_bytes)

def run_server(host="0.0.0.0", port=8000):
    httpd = HTTPServer((host, port), SimpleRequestHandler)
    print(f"Serving on {host}:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
