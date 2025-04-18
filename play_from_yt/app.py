from flask import Flask, render_template, request, jsonify
from youtubesearchpython import VideosSearch

app = Flask(__name__)

# Function to search YouTube using youtubesearchpython
def search_youtube(query, max_results=10):
    results = []
    try:
        # Search using youtubesearchpython (searches for videos on YouTube)
        videos_search = VideosSearch(query, limit=max_results)
        search_results = videos_search.result().get('result', [])
        
        for item in search_results:
            title = item.get('title', 'Sem título')
            url = item.get('link', 'Sem link')
            thumbnail = item.get('thumbnails', [{}])[0].get('url', '')  # Extracting the thumbnail URL
            author_info = item.get('channel', {})
            author = author_info.get('name', 'Unknown')  # Extracting the author (channel name)
            duration = item.get('duration', '00:00')  # Extracting the video duration
            
            results.append({
                "title": title,
                "url": url,
                "thumbnail": thumbnail,  # Include the thumbnail URL
                "author": author,        # Include the author name
                "duration": duration     # Include the duration
            })
    except Exception as e:
        print(f"Error occurred: {e}")
    return results

# Endpoint for search suggestions
@app.route("/search_suggestions", methods=["GET"])
def search_suggestions():
    query = request.args.get('query')
    if query:
        results = search_youtube(query, max_results=5)  # Limit the number of results
        return jsonify(results)
    return jsonify([])

# Main endpoint to display the page
@app.route("/", methods=["GET", "POST"])
def index():
    results = []  # Initialize results as empty
    if request.method == "POST":
        query = request.form.get("query")
        if query:
            results = search_youtube(query)  # Search based on user input
    return render_template("index.html", results=results)

if __name__ == "__main__":
    app.run(debug=True)
