from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# =========================
# CSV 読み込み
# =========================

# movies_100k.csv（| 区切り）
movies = pd.read_csv(
    "movies_100k.csv",
    sep="|",
    encoding="latin-1"
)

# ratings_100k.csv（タブ区切り）
ratings = pd.read_csv(
    "ratings_100k.csv",
    sep="\t",
    header=None,
    names=["user_id", "movie_id", "rating", "timestamp"]
)

# =========================
# 前処理
# =========================

# 平均評価を計算
rating_mean = ratings.groupby("movie_id")["rating"].mean().reset_index()
rating_mean.columns = ["movie_id", "avg_rating"]

# movies に平均評価を結合
movies = movies.merge(rating_mean, on="movie_id", how="left")

# ジャンル列（Action 以降）
GENRE_COLUMNS = movies.columns[5:]

# ★ NaN を 0 に補完（ジャンル列に欠損がある場合の対策）
movies[GENRE_COLUMNS] = movies[GENRE_COLUMNS].fillna(0)

# =========================
# ルーティング
# =========================

@app.route("/")
def index():
    movie_titles = movies["movie_title"].tolist()
    return render_template("index.html", movies=movie_titles)


@app.route("/recommend", methods=["POST"])
def recommend():
    selected_movies = request.form.getlist("movies")

    # ===== 未選択：人気順 =====
    if len(selected_movies) == 0 or all(m == "" for m in selected_movies):
        recs = (
            movies.sort_values("avg_rating", ascending=False)
            .head(5)["movie_title"]
            .tolist()
        )
        reason = "映画が選択されていないため、全体で評価の高い映画を表示しています。"

    # ===== 選択あり：コンテンツベース =====
    else:
        # 選択映画のジャンル傾向を集約
        genre_score = {genre: 0 for genre in GENRE_COLUMNS}

        for title in selected_movies:
            if title == "":
                continue
            row = movies[movies["movie_title"] == title]
            for genre in GENRE_COLUMNS:
                genre_score[genre] += int(row[genre].values[0])

        # スコアが高いジャンル抽出
        selected_genres = [g for g, v in genre_score.items() if v > 0]

        # 同ジャンル映画を抽出
        filtered = movies.copy()
        for genre in selected_genres:
            filtered = filtered[filtered[genre] == 1]

        recs = (
            filtered.sort_values("avg_rating", ascending=False)
            .head(5)["movie_title"]
            .tolist()
        )

        reason = "選択された映画のジャンル傾向に基づいておすすめしています。"

    return render_template(
        "result.html",
        recommendations=recs,
        reason=reason
    )


if __name__ == "__main__":
    app.run(debug=True)
