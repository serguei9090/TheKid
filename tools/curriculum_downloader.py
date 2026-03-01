import argparse
import os
import wikipedia
import markdownify

LIBRARY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "library"))

def download_wikipedia_article(topic: str, category: str):
    """
    Downloads a Wikipedia article by topic, converts the summary and content 
    into clean Markdown, and saves it to the library.
    """
    print(f"Searching Wikipedia for: {topic}...")
    try:
        # Search for the best match
        search_results = wikipedia.search(topic)
        if not search_results:
            print(f"  -> No results found for '{topic}'.")
            return

        best_match = search_results[0]
        page = wikipedia.page(best_match, auto_suggest=False)
        
        print(f"  -> Found: {page.title}")
        
        # Convert HTML to Markdown (Wikipedia python library returns plaintext, 
        # but we can structure it nicely for The Kid).
        md_content = f"# {page.title}\n"
        md_content += f"*Context: {category}, Educational, Reference*\n\n"
        md_content += f"## Summary\n{page.summary}\n\n"
        
        # Add a snippet of the main content to avoid overwhelming the LLM Teacher,
        # but give enough for solid quadruplet extraction.
        content_snippet = "\n".join(page.content.split("\n")[:20]) 
        md_content += f"## Core Facts\n{content_snippet}\n"

        # Create category folder if it doesn't exist
        cat_dir = os.path.join(LIBRARY_DIR, category.lower())
        os.makedirs(cat_dir, exist_ok=True)

        # Save the file
        safe_title = page.title.replace(" ", "_").replace("/", "-")
        file_path = os.path.join(cat_dir, f"{safe_title}.md")
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(md_content)
            
        print(f"  -> Saved successfully to: {file_path}")

    except wikipedia.exceptions.DisambiguationError as e:
        print(f"  -> Topic is too broad. Options include: {e.options[:5]}")
    except Exception as e:
        print(f"  -> Error downloading {topic}: {e}")

def main():
    parser = argparse.ArgumentParser(description="The Kid - Curriculum Downloader")
    parser.add_argument("--topic", type=str, help="Specific topic to download from Wikipedia (e.g. 'Photosynthesis')")
    parser.add_argument("--category", type=str, default="General", help="Folder to save the file in (e.g. 'Science')")
    parser.add_argument("--batch", type=str, help="Comma separated list of topics to download")
    
    args = parser.parse_args()

    # Ensure base library exists
    os.makedirs(LIBRARY_DIR, exist_ok=True)

    if args.batch:
        topics = [t.strip() for t in args.batch.split(",")]
        print(f"Starting batch download of {len(topics)} topics...")
        for t in topics:
            download_wikipedia_article(t, args.category)
    elif args.topic:
        download_wikipedia_article(args.topic, args.category)
    else:
        print("Please provide a --topic or --batch. Use -h for help.")

if __name__ == "__main__":
    main()
