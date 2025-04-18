from youtubesearchpython import VideosSearch

def procurar_musicas():
    consulta = input("Digite o nome da música ou artista: ")
    videos_search = VideosSearch(consulta, limit=10)
    resultados = videos_search.result().get('result', [])

    print(f"\nResultados para: {consulta}\n")
    for resultado in resultados:
        titulo = resultado.get('title', 'Sem título')
        link = resultado.get('link', 'Sem link')
        print(f"Título: {titulo}")
        print(f"Link: {link}\n")

if __name__ == "__main__":
    procurar_musicas()
