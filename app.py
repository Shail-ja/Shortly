from flask import Flask, request, jsonify, redirect, render_template
import random, string
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                 (short_code TEXT PRIMARY KEY, long_url TEXT, clicks INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()    

def generate_code(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/shorten', methods=['POST'])
def shorten():
    data = request.get_json()
    custom = data.get("custom")
    if custom:
        short_code = custom
    else:
        short_code = generate_code()

    long_url = data.get("url")

    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("SELECT * FROM urls WHERE short_code=?", (short_code,))
    if c.fetchone():
        conn.close()
        return jsonify({"error": "Custom code already exists"}), 400
    
    c.execute("INSERT INTO urls (short_code, long_url, clicks) VALUES (?, ?, 0)", (short_code, long_url))
    conn.commit()
    conn.close()

    return jsonify({
        "short_url": f"http://127.0.0.1:5000/{short_code}"
    })

@app.route('/<short_code>')
def redirect_url(short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("SELECT long_url, clicks FROM urls WHERE short_code=?", (short_code,))
    result = c.fetchone()

    if result:
        long_url, clicks = result
        c.execute(
            "UPDATE urls SET clicks = ? WHERE short_code = ?", 
            (clicks + 1, short_code)
        )
        conn.commit()
        conn.close()
        return redirect(long_url)
    else:
        conn.close()
        return jsonify({"error": "URL not found"}), 404

@app.route('/stats/<short_code>')
def stats(short_code):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("SELECT long_url, clicks FROM urls WHERE short_code=?", (short_code,))
    result = c.fetchone()
    conn.close()

    if result:
        long_url, clicks = result
        return jsonify({
            "long_url": long_url,
            "clicks": clicks
        })
    else:
        return jsonify({"error": "URL not found"}), 404
    
@app.route("/all")
def view_all():
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()
    c.execute("SELECT short_code, long_url, clicks FROM urls")
    urls = c.fetchall()
    conn.close()

    return render_template('all_urls.html', urls=urls)

@app.route("/delete/<short_code>", methods=["POST"])
def delete_url(short_code):
    import sqlite3

    conn = sqlite3.connect("urls.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM urls WHERE short_code=?", (short_code,))
    conn.commit()
    conn.close()

    return redirect("/all")

if __name__ == '__main__':
    init_db()
    app.run()