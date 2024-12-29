from nba_api.stats.endpoints import playercareerstats, teamyearbyyearstats
from nba_api.live.nba.endpoints import scoreboard
from nba_api.stats.static import players, teams
import pickle
import base64
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
    pickled = pickle.dumps(live_games)
    return base64.b64encode(pickled)

def get_data(type, id):
    settings = {}
    if type == "team":
        data = teamyearbyyearstats.TeamYearByYearStats(team_id=id)
        settings["data"] = data.get_data_frames()[0]
        settings["name"] = teams.find_team_name_by_id(id)
        settings["final_stats"] = data.get_normalized_dict()["TeamStats"]
    elif type == "player":
        data = playercareerstats.PlayerCareerStats(player_id=id)
        settings["data"] = data.get_data_frames()[0]
        settings["name"] = players.find_player_by_id(id)
        settings["final_stats"] = data.get_normalized_dict()["SeasonTotalsRegularSeason"]
    pickled = pickle.dumps(settings)
    return base64.b64encode(pickled)

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

        response_bytes = body_data

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
