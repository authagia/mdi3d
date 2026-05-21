import os
import random
import http.server
import socketserver

# --- 設定 ---
PORT = 8000
# SVGファイルが保存されているディレクトリのパス（サーバーファイルと同じ場所なら '.'）
SVG_DIR = "./mdi_svg" 

print("SVGファイルのリストを読み込み中...")
# 起動時に一度だけファイルリストを取得してキャッシュ（高速化のため）
try:
    SVG_FILES = [f for f in os.listdir(SVG_DIR) if f.lower().endswith('.svg')]
    print(f"合計 {len(SVG_FILES)} 個のSVGファイルを検出しました。")
except FileNotFoundError:
    print(f"エラー: ディレクトリ '{SVG_DIR}' が見つかりません。")
    SVG_FILES = []

class RandomSVGHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # ルート（/）へのアクセス、または index.html へのアクセスの場合
        if self.path == '/' or self.path == '/index.html':
            if not SVG_FILES:
                self.send_error(500, "No SVG files found in the directory.")
                return

            # ランダムに16個選出（重複なし。もし全体が16個未満ならあるだけ選ぶ）
            num_to_select = min(28, len(SVG_FILES))
            selected_files = random.sample(SVG_FILES, num_to_select)

            # HTMLの構築
            html_content = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Random SVG Gallery</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; margin: 20px; }
        h1 { text-align: center; color: #333; }
        /* ボタンのコンテナとスタイル */
        .btn-container {
            text-align: center;
            margin: 20px 0 30px 0;
        }
        .reload-btn {
            background-color: #0f1b33;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 16px;
            font-weight: bold;
            border-radius: 25px;
            cursor: pointer;
            box-shadow: 0 4px 6px rgba(15,23,55,0.2);
            transition: all 0.2s ease;
        }
        .reload-btn:hover {
            background-color: #0056b3;
            transform: translateY(-1px);
            box-shadow: 0 6px 8px rgba(0,123,255,0.3);
        }
        .reload-btn:active {
            transform: translateY(1px);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        .card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }
        .card img {
            width: 100%;
            height: auto;
            max-height: 120px;
            object-fit: contain;
        }
        .filename {
            margin-top: 10px;
            font-size: 11px;
            color: #666;
            word-break: break-all;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>Random 16 SVGs</h1>
    <div class="grid">
"""
            # 選択されたSVGを <img> タグとして埋め込み
            for filename in selected_files:
                # SVGファイルへのURLパス（ディレクトリ名 + ファイル名）
                file_url = f"/{SVG_DIR.strip('./')}/{filename}"
                html_content += f"""
        <div class="card">
            <img src="{file_url}" alt="{filename}">
            <div class="filename">{filename}</div>
        </div>"""

            html_content += """
    </div>
    <div class="btn-container">
        <button class="reload-btn" onclick="window.location.reload(true);">他の画像を見る ↻</button>
    </div>
</body>
</html>
"""
            # レスポンスの送信
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            # ブラウザにキャッシュさせない設定（リロード時に確実にランダム変更するため）
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        
        else:
            # SVGファイルの実体などを要求された場合は、通常のファイルサーバーとして挙動
            super().do_GET()

# サーバーの起動
with socketserver.TCPServer(("", PORT), RandomSVGHandler) as httpd:
    print(f"サーバーが起動しました: http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止します。")