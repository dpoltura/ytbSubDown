import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
import openai

# Configurez votre clé API YouTube
api_key = 'VOTRE CLE API YOUTUBE'
youtube = build('youtube', 'v3', developerKey=api_key)

# Configurez votre clé API OpenAI
openai.api_key = 'VOTRE CLE API OPENAI'

def get_video_links(keyword, max_results):
    try:
        request = youtube.search().list(
            q=keyword,
            type='video',
            part='id',
            maxResults=max_results
        )
        response = request.execute()
        
        video_links = []
        for item in response['items']:
            video_links.append(f"https://www.youtube.com/watch?v={item['id']['videoId']}")
        
        return video_links
    except HttpError as e:
        print(f"Une erreur s'est produite lors de la recherche pour '{keyword}': {e}")
        return []

def get_video_subtitles(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr', 'en'])
        return ' '.join([entry['text'] for entry in transcript])
    except TranscriptsDisabled:
        return "Sous-titres non disponibles pour cette vidéo."
    except Exception as e:
        return f"Erreur lors de la récupération des sous-titres : {str(e)}"

def correct_subtitles_with_chatgpt(subtitles):
    prompt = f"""Voici les sous-titres d'une vidéo YouTube. Corrige l'ortographe et les incohérences, 
    tout en veillant a bien conserver le sens original. Voici les sous-titres :

    {subtitles}

    Sous-titres corrigés :"""

    try:
        response = openai.completions.create(
            model="gpt-3.5-turbo",
            prompt=[
                {"role": "system", "content": "Vous êtes un assistant spécialisé dans la correction et l'amélioration de sous-titres."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"Erreur lors de la correction des sous-titres avec ChatGPT : {str(e)}")
        return subtitles  # Retourne les sous-titres originaux en cas d'erreur

def save_links_and_subtitles_to_file(links, filename):
    with open(filename, 'w', encoding='utf-8') as file:
        for link in links:
            file.write(f"{link}\n")
            video_id = link.split('=')[-1]
            subtitles = get_video_subtitles(video_id)
            corrected_subtitles = correct_subtitles_with_chatgpt(subtitles)
            file.write(f"Sous-titres corrigés : {corrected_subtitles}\n\n")

def main():
    keywords_input = input("Entrez les mots-clés séparés par des virgules : ")
    keywords = [k.strip() for k in keywords_input.split(',')]

    total_results = int(input("Entrez le nombre total de résultats souhaités : "))
    results_per_keyword = max(1, total_results // len(keywords))

    output_file = 'youtube_links_and_corrected_subtitles.txt'
    all_links = []

    for keyword in keywords:
        print(f"Recherche de vidéos pour le mot-clé : {keyword}")
        links = get_video_links(keyword, results_per_keyword)
        all_links.extend(links)
        print(f"{len(links)} liens trouvés pour '{keyword}'")

        if len(all_links) >= total_results:
            all_links = all_links[:total_results]
            break

    if all_links:
        print("\nRécupération et correction des sous-titres en cours...")
        save_links_and_subtitles_to_file(all_links, output_file)
        print(f"\nUn total de {len(all_links)} liens et leurs sous-titres corrigés ont été enregistrés dans {output_file}")
    else:
        print("\nAucun lien n'a pu être récupéré. Veuillez vérifier votre clé API et les paramètres de votre projet Google.")

if __name__ == "__main__":
    main()