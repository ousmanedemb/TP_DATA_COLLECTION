import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
from requests import get
import base64
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px

# Définir la configuration de la page pour une mise en page large
st.set_page_config(layout="wide")

# Fonction Background
def add_bg_from_local(image_file):
    with open(image_file, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    st.markdown(
    f"""
    <style>
    .stApp {{
        background-image: url(data:image/{"jpg"};base64,{encoded_string.decode()});
        background-size: cover
    }}
    </style>
    """,
    unsafe_allow_html=True
    )

@st.cache_data
def scrap_page(num_pages, page_type):
    results = []

    for page in range(1, num_pages + 1):
        url = f'https://www.expat-dakar.com/{page_type}?page={page}'
        response = get(url)
        if response.status_code == 200 or response.status_code == 429:
            soup = BeautifulSoup(response.text, 'html.parser')
            containers = soup.find_all('div', class_ = 'listings-cards__list-item')
            for container in containers:
                try:
                    details = container.find('div', class_ = 'listing-card__header__title').text.strip()
                    etat = container.find('span', class_ = 'listing-card__header__tags__item').text.strip()
                    adresse = container.find('div', class_ = 'listing-card__header__location').text.replace('\n','').strip()
                    prix = container.find('span', class_ = 'listing-card__price').text.strip().split('\n\n')[0].replace('\u202f','').replace(' F Cfa','')
                    image_lien = container.find('img', class_ = 'listing-card__image__resource')['src']
                    obj = {
                        'details': details,
                        'etat': etat,
                        'adresse': adresse,
                        'prix': prix,
                        'image_lien': image_lien
                    }
                    results.append(obj)
                except:
                    pass
        else:
            #st.write(f"Échec du scraping de la page {page}. Code de statut HTTP: {response.status_code}")
    data = pd.DataFrame(results)
    return data

def display_result(df):
    # Afficher les résultats à l'écran
    st.write('Data dimension: ' + str(df.shape[0]) + ' rows and ' + str(df.shape[1]) + ' columns.')
    st.dataframe(df)

    # Ajouter un lien de téléchargement pour le DataFrame
    csv = df.to_csv().encode('utf-8')

    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name='data.csv',
        mime='text/csv')
    


def main():
    st.markdown("<h1 style='text-align: center; font-size: 30px;'>Application de Scraping de Données Groupe 7</h1>", unsafe_allow_html=True)
    add_bg_from_local('24049.jpg')

    st.sidebar.title('User Input Features')
    # Options pour la sélection du nombre de pages
    options = [i for i in range(1, 101)]

    # Sélection du nombre de pages à scraper
    num_pages = st.sidebar.selectbox("Pages indexes", options)

    # Specifier l'url à scraper
    page_type = st.sidebar.selectbox("Sélectionnez la page à scraper", ('Scrape data using beautifulSoup','Download scraped data','Dashbord of the data','Fill the form'))

    
    if page_type == 'Scrape data using beautifulSoup':
        refrigerateurs = scrap_page(num_pages, 'refrigerateurs-congelateurs')
        climatisation = scrap_page(num_pages, 'climatisation')
        cuisinieres = scrap_page(num_pages, 'cuisinieres-fours')
        machines = scrap_page(num_pages, 'machines-a-laver')
        contenu = pd.DataFrame()

        # Bouton pour afficher les résultats
        col1, col2, col3, col4 = st.columns([1,1,1,1])

        with col1:
            if st.button("Refrigerateurs data"):
                contenu = refrigerateurs
                st.write(refrigerateurs.shape)
        with col2:
            if st.button("Climatisation data"):
                contenu = climatisation
                st.write(climatisation.shape)
        with col3:
            if st.button("Cuisinieres data"):
                contenu = cuisinieres
                st.write(cuisinieres.shape)
        with col4:
            if st.button("Machine à laver data"):
                contenu = machines
                st.write(machines.shape)

        # Afficher st.write en pleine largeur
        with st.expander("Résultat", expanded=True):
            if contenu.shape[0] != 0:
                display_result(contenu)

    elif page_type == 'Dashbord of the data':
        st.set_option('deprecation.showPyplotGlobalUse', False)
        df1 = scrap_page(num_pages, 'refrigerateurs-congelateurs')
        df2 = scrap_page(num_pages, 'machines-a-laver')
        # Convertir la colonne 'Prix' en type numérique
        df1['prix'] = pd.to_numeric(df1['prix'], errors='coerce')
        df2['prix'] = pd.to_numeric(df2['prix'], errors='coerce')
        # Sélectionner les cinq produits les plus chers
        top_5_products_refrigerateurs = df1.nlargest(5, 'prix')
        top_5_products_machine_laver = df2.nlargest(5, 'prix')

        col1, col2 = st.columns([1,1])
        with col1:
            # Définir une palette de couleurs
            colors = px.colors.qualitative.Pastel
            # Afficher le graphique des prix des produits
            fig_prix = px.bar(top_5_products_refrigerateurs, x="details", y="prix", title="Cinq produits les plus chers (Categories : Refrigerateurs)", labels={"details": "Produit", "prix": "Prix (FCFA)"}, color="prix", color_continuous_scale=colors)
            #fig_prix.update_layout(xaxis={'categoryorder':'total descending'})
            fig_prix.update_xaxes(tickangle=45, tickfont=dict(size=9))
            st.plotly_chart(fig_prix, use_container_width=True)
            #------------------------------------------
            fig_prix = px.bar(top_5_products_machine_laver, x="details", y="prix", title="Cinq produits les plus chers (Categories : Machine à laver)", labels={"details": "Produit", "prix": "Prix (FCFA)"}, color="prix", color_continuous_scale=colors)
            #fig_prix.update_layout(xaxis={'categoryorder':'total descending'})
            fig_prix.update_xaxes(tickangle=45, tickfont=dict(size=9))
            st.plotly_chart(fig_prix, use_container_width=True)
            #------------------------------------------
            # Calculer le nombre de produits par adresse
            products_per_address = df1['adresse'].value_counts().reset_index()
            products_per_address.columns = ['Adresse', 'Nombre de produits']
            # Définir une palette de couleurs
            colors = px.colors.qualitative.Pastel
            # Créer un histogramme pour visualiser le nombre de produits par adresse
            fig = px.bar(products_per_address, x='Adresse', y='Nombre de produits', title='Nombre de produits par adresse (Categories : Refrigerateurs)', color='Adresse', color_discrete_sequence=colors)
            # Afficher le graphique
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            # Graphique de la répartition des états des produits
            couleurs = px.colors.qualitative.Set3
            fig_etat = px.pie(df1, names='etat', title='Répartition des états des produits (Categories : Refrigerateurs)', color_discrete_sequence=couleurs)
            st.plotly_chart(fig_etat, use_container_width=True)
            #-----------------------------------------
            couleurs = px.colors.qualitative.Set3
            fig_etat = px.pie(df2, names='etat', title='Répartition des états des produits (Categories : Machine à laver)', color_discrete_sequence=couleurs)
            st.plotly_chart(fig_etat, use_container_width=True)
            #-----------------------------------------
            # Calculer le nombre de produits par adresse
            products_per_address = df2['adresse'].value_counts().reset_index()
            products_per_address.columns = ['Adresse', 'Nombre de produits']
            # Définir une palette de couleurs
            colors = px.colors.qualitative.Pastel
            # Créer un histogramme pour visualiser le nombre de produits par adresse
            fig = px.bar(products_per_address, x='Adresse', y='Nombre de produits', title='Nombre de produits par adresse (Categories : Machine à laver)', color='Adresse', color_discrete_sequence=colors)
            # Afficher le graphique
            st.plotly_chart(fig, use_container_width=True)
    elif page_type == 'Fill the form':
        import streamlit.components.v1 as components
        st.write("TEST")
        html_content = """
            <iframe src="https://ee.kobotoolbox.org/i/y3pfGxMz" width="1000" height = "750"></iframe>
            """
        st.markdown(
            f'<div style="max-width: 1000px">{html_content}</div>', 
            unsafe_allow_html=True
        )


if __name__ == "__main__":
    main()