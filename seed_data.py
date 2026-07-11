import os
import file_manager

def seed():
    print("Iniciando sembrado de proyectos y libros...")
    
    # 1. Proyecto: Modelar y Juegos
    p1_title = "Uso de las matemáticas y la física para modelar cosas o ser mejor a juegos"
    p1_desc = "Explorar modelos matemáticos y físicos aplicados a la toma de decisiones, predicciones, teoría de juegos y sistemas complejos."
    p1_id = file_manager.slugify(p1_title)
    
    file_manager.ensure_project_note(
        titulo=p1_title,
        descripcion=p1_desc,
        estado="activo",
        etiqueta="Juegos"
    )
    
    # Libros del Proyecto 1
    p1_books = [
        # Construir Intuición
        {"titulo": "How to solve it", "autor": "George Polya", "sec": "Construir Intuición", "cat": "Matemáticas"},
        {"titulo": "Guesstimation", "autor": "Lawrence Weinstein & John A. Adam", "sec": "Construir Intuición", "cat": "Física"},
        {"titulo": "Fooled By Randomness", "autor": "Nassim Nicholas Taleb", "sec": "Construir Intuición", "cat": "Probabilidad"},
        
        # Modelar el mundo
        {"titulo": "Street Fighting Mathematics", "autor": "Sanjoy Mahajan", "sec": "Modelar el mundo", "cat": "Matemáticas"},
        {"titulo": "The signal and the Noise", "autor": "Nate Silver", "sec": "Modelar el mundo", "cat": "Estadística"},
        {"titulo": "The Black Swan", "autor": "Nassim Nicholas Taleb", "sec": "Modelar el mundo", "cat": "Sistemas Complejos"},
        
        # Estrategia y Decisión
        {"titulo": "The art of Strategy", "autor": "Avinash K. Dixit & Barry J. Nalebuff", "sec": "Estrategia y Decisión", "cat": "Teoría de Juegos"},
        {"titulo": "The mathematics of poker", "autor": "Bill Chen & Jerrod Ankenman", "sec": "Estrategia y Decisión", "cat": "Teoría de Juegos"},
        
        # Sistemas Complejos
        {"titulo": "Antifragile", "autor": "Nassim Nicholas Taleb", "sec": "Sistemas Complejos", "cat": "Sistemas Complejos"},
        {"titulo": "The physics of Wall Street", "autor": "James Owen Weatherall", "sec": "Sistemas Complejos", "cat": "Economía / Física"},
        
        # Profundización matemática
        {"titulo": "Information theory, Inference, and Learning Algorithms", "autor": "David J.C. MacKay", "sec": "Profundización matemática", "cat": "Matemáticas"}
    ]
    
    for b in p1_books:
        file_manager.ensure_book_note(
            titulo=b["titulo"],
            autor=b["autor"],
            categoria=b["cat"],
            proyecto_id=p1_id,
            seccion_proyecto=b["sec"]
        )
        
    # 2. Proyecto: Automatizar mi estudio
    p2_title = "Automatizar mi estudio"
    p2_desc = "Recopilación de exámenes, transcripción, apuntes, resolución de ejercicios, integración de Obsidian y seguimiento automatizado de errores mediante Inteligencia Artificial."
    p2_id = file_manager.slugify(p2_title)
    
    file_manager.ensure_project_note(
        titulo=p2_title,
        descripcion=p2_desc,
        estado="activo",
        etiqueta="Estudio"
    )
    
    # 3. Proyecto: Entender cómo funciona la IA
    p3_title = "Entender como funciona la IA"
    p3_desc = "Estudiar a fondo el procesamiento del lenguaje natural, redes neuronales, transformers y arquitecturas deep learning desde cero."
    p3_id = file_manager.slugify(p3_title)
    
    file_manager.ensure_project_note(
        titulo=p3_title,
        descripcion=p3_desc,
        estado="activo",
        etiqueta="IA"
    )
    
    # Libros del Proyecto 3
    p3_books = [
        {"titulo": "Build a large language model (from Scratch)", "autor": "Sebastian Raschka", "sec": "Modelos de Lenguaje", "cat": "IA / LLMs"},
        {"titulo": "Natural Language Processing with transformers", "autor": "Lewis Tunstall, Leandro von Werra & Thomas Wolf", "sec": "Transformers", "cat": "IA / NLP"},
        {"titulo": "Speech and Language Processing", "autor": "Dan Jurafsky & James H. Martin", "sec": "NLP Tradicional", "cat": "IA / NLP"},
        {"titulo": "Deep Learning", "autor": "Ian Goodfellow, Yoshua Bengio & Aaron Courville", "sec": "Redes Neuronales", "cat": "IA / Deep Learning"}
    ]
    
    for b in p3_books:
        file_manager.ensure_book_note(
            titulo=b["titulo"],
            autor=b["autor"],
            categoria=b["cat"],
            proyecto_id=p3_id,
            seccion_proyecto=b["sec"]
        )
        
    print("¡Sembrado completado con éxito!")

if __name__ == "__main__":
    seed()
