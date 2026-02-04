import streamlit as st
import pandas as pd
import plotly.express as px

# 1. KONFIGURATION & DESIGN
st.set_page_config(page_title="Olympia Dashboard", layout="wide")

def benutzerdefiniertes_css():
    """Definiert das Tabellen-Styling für bessere Lesbarkeit"""
    st.markdown("""
        <style>
                .olympia-tabelle {
                    margin-left: auto; margin-right: auto;
                    border-collapse: collapse; width: fit-content; min-width: 65%;
                    color: var(--text-color); background-color: transparent;
                }
                .olympia-tabelle th {
                    background-color: rgba(128, 128, 128, 0.1);
                    padding: 12px 25px; border-bottom: 2px solid #555;
                    text-align: center !important;
                }
                .olympia-tabelle td {
                    padding: 10px 20px; border-bottom: 1px solid rgba(128, 128, 128, 0.2);
                    text-align: center !important;
                }
                </style>
                """, unsafe_allow_html=True)
    
# 2. DATEN UND FORMATIERUNGSHELFER
@st.cache_data
def lade_daten():
    return pd.read_csv('dataset_olympics_cleaned.csv')

def hole_rang_anzeige(zeile):
    """Wandelt Medaillen-Texte in Icons um und bereinigt Rang-Nummern."""
    medaille = str(zeile['Medal'])
    rang = str(zeile['rank_position'])
    if medaille == "Gold": return "🥇"
    if medaille == "Silber": return "🥈"
    if medaille == "Bronze": return "🥉"
    if pd.isna(zeile['rank_position']) or rang.lower() == "nan": return "-"
    try:
        return str(int(float(rang)))
    except:
        return rang
    
def zeige_html_tabelle(dataframe):
    """Gibt eine Tabelle ohne Index-Spalte im definierten CSS-Stil aus"""
    html = dataframe.to_html(index=False, classes='olympia-tabelle', escape=False)
    st.markdown(html, unsafe_allow_html=True)

# 3. DIE DIREKTEN SEITENFUNKTIONEN

def zeige_top_athleten(df):
    st.title("🏅Bestenliste (Einzelwettbewerbe)")

    # Filter: Nur Einzelathleten und nur Medaillengewinner
    df_gefiltert = df[(df['participant_type'] == 'Athlete') & 
                      (df['Medal'].isin(['Gold', 'Silber', 'Bronze']))].copy()

    def berechne_statistik(daten):
        stats = daten.groupby(['Name', 'Sport', 'Season'])['Medal'].value_counts().unstack(fill_value=0)
        for col in ['Gold', 'Silber', 'Bronze']:
            if col not in stats.columns:
                stats[col] = 0
        stats['Gesamt'] = stats['Gold'] + stats['Silber'] + stats['Bronze']
        stats = stats.sort_values(by=['Gold', 'Silber', 'Bronze'], ascending=False).reset_index()
        # Spalte heißt jetzt Rang
        stats.insert(0, 'Rang', range(1, len(stats) + 1))
        return stats

    tab1, tab2, tab3 = st.tabs(["☀️ Sommer", "❄️ Winter", "🏆 Gesamt-Ranking"])

    def erstelle_ansicht(daten_quelle, titel, key_suffix):
        
        anzeige_stats = berechne_statistik(daten_quelle)
        
        if not anzeige_stats.empty:
            top_5 = anzeige_stats.head(5)
            
            # Diagramm ohne "value" und "variable" Beschriftung
            fig = px.bar(
                top_5, 
                x='Name', 
                y=['Gold', 'Silber', 'Bronze'],
                title=f"Top 5 Athleten:",
                barmode='group',
                color_discrete_map={'Gold': '#FFD700', 'Silber': '#C0C0C0', 'Bronze': '#CD7F32'},
                # Labels überschreiben die Standard-Namen (value/variable)
                labels={'value': 'Anzahl Medaillen', 'variable': 'Medaillen-Typ'}
            )
            
            fig.update_xaxes(tickmode='array', tickvals=top_5['Name'], tickangle=-45, title="")
            fig.update_yaxes(title="Anzahl")
            
            # Legende schöner machen
            fig.update_layout(legend_title_text='Medaille')
            
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{key_suffix}")

            st.subheader("Weitere Platzierungen")
            rest = anzeige_stats.iloc[5:]
            
            # Spaltenreihenfolge mit "Rang"
            spalten = ['Rang', 'Name', 'Sport', 'Season', 'Gold', 'Silber', 'Bronze', 'Gesamt']
            
            st.dataframe(
                rest[spalten], 
                use_container_width=True, 
                hide_index=True,
                height=800,
                key=f"df_{key_suffix}"
            )
        else:
            st.write("Keine Daten verfügbar.")

    with tab1:
        erstelle_ansicht(df_gefiltert[df_gefiltert['Season'] == 'Summer'], "Sommerspiele", "sommer")
    with tab2:
        erstelle_ansicht(df_gefiltert[df_gefiltert['Season'] == 'Winter'], "Winterspiele", "winter")
    with tab3:
        erstelle_ansicht(df_gefiltert, "Gesamtübersicht", "gesamt")

def zeige_ewigen_medaillenspiegel(df_global):
    """
    Berechnet die Medaillen über die gesamte Zeitgeschichte ohne Jahresfilter.
    Getrennt nach Sommer und Winter via Tabs.
    """
    st.title("🏆 Ewiger Medaillenspiegel")
        
    t_sommer, t_winter = st.tabs(["☀️ Sommer", "❄️ Winter"])
    
    with t_sommer:
        # Flexibler Filter für Sommer (deckt 'Sommer' und 'Summer' ab)
        df_s = df_global[df_global['Season'].isin(['Sommer', 'Summer'])].dropna(subset=['Medal']).copy()
        if not df_s.empty:
            ewig_s = df_s.pivot_table(index='Team', columns='Medal', aggfunc='size', fill_value=0)
            for m in ['Gold', 'Silber', 'Bronze']:
                if m not in ewig_s.columns: ewig_s[m] = 0
            ewig_s = ewig_s[['Gold', 'Silber', 'Bronze']]
            ewig_s['Gesamt'] = ewig_s.sum(axis=1)
            ewig_s = ewig_s.sort_values(by=['Gold', 'Silber', 'Bronze'], ascending=False).reset_index()
            ewig_s.columns = ['Land', '🥇', '🥈', '🥉', 'Gesamt']
            zeige_html_tabelle(ewig_s)
        else:
            st.warning("Keine Daten für Sommerspiele gefunden. Prüfe die Spalte 'Season' in deiner CSV.")

    with t_winter:
        # Flexibler Filter für Winter (deckt 'Winter' ab)
        df_w = df_global[df_global['Season'] == 'Winter'].dropna(subset=['Medal']).copy()
        if not df_w.empty:
            ewig_w = df_w.pivot_table(index='Team', columns='Medal', aggfunc='size', fill_value=0)
            for m in ['Gold', 'Silber', 'Bronze']:
                if m not in ewig_w.columns: ewig_w[m] = 0
            ewig_w = ewig_w[['Gold', 'Silber', 'Bronze']]
            ewig_w['Gesamt'] = ewig_w.sum(axis=1)
            ewig_w = ewig_w.sort_values(by=['Gold', 'Silber', 'Bronze'], ascending=False).reset_index()
            ewig_w.columns = ['Land', '🥇', '🥈', '🥉', 'Gesamt']
            zeige_html_tabelle(ewig_w)
        else:
            st.warning("Keine Daten für Winterspiele gefunden.")

def zeige_athleten_profil(df_global):
    """Direkte Funktion für die intuitive Athletensuche."""
    st.title("👤 Athleten-Biografie & Karriere")

    alle_athleten = sorted(df_global['Name'].unique())
    suche = st.selectbox(
        "Suche oder wähle einen Athleten aus:",
        options=[""] + alle_athleten,
        format_func=lambda x: "Bitte Namen eingeben..." if x == "" else x
    )

    if suche != "":
        ergebnisse = df_global[df_global['Name'] == suche].copy()
        if not ergebnisse.empty:
            st.header(f"Olympia-Statistik: {suche}")
            medaillen_daten = ergebnisse.dropna(subset=['Medal'])
            gold = len(medaillen_daten[medaillen_daten['Medal'] == 'Gold'])
            silber = len(medaillen_daten[medaillen_daten['Medal'] == 'Silber'])
            bronze = len(medaillen_daten[medaillen_daten['Medal'] == 'Bronze'])

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Starts", len(ergebnisse))
            c2.metric("🥇 Gold", gold)
            c3.metric("🥈 Silber", silber)
            c4.metric("🥉 Bronze", bronze)

            st.divider()
            ergebnisse['Rang'] = ergebnisse.apply(hole_rang_anzeige, axis=1)
            historie = ergebnisse[['Year', 'Sport', 'event_title', 'Rang', 'Team']].sort_values('Year', ascending=False)
            historie.columns = ['Jahr', 'Sportart', 'Disziplin', 'Rang', 'Land']
            zeige_html_tabelle(historie)

def zeige_disziplin_analyse(df_jahr, jahr):
    """Analysiert spezifische Sportarten eines gewählten Jahres."""
    st.title("Disziplin-Analyse")
    sportarten = sorted(df_jahr["Sport"].unique())
    sport_wahl = st.sidebar.selectbox("Sportart:", options=sportarten)
    
    df_sport = df_jahr[df_jahr["Sport"] == sport_wahl]
    disziplinen = sorted(df_sport["event_title"].unique())
    disziplin_wahl = st.sidebar.selectbox("Disziplin:", options=["Alle Disziplinen"] + disziplinen)

    if disziplin_wahl == "Alle Disziplinen":
        t1, t2 = st.tabs(["📊 Tabelle", "📈 Diagramm"])
        df_med = df_sport.dropna(subset=['Medal']).copy()
        if not df_med.empty:
            t = df_med.pivot_table(index='Team', columns='Medal', aggfunc='size', fill_value=0)
            for m in ['Gold', 'Silber', 'Bronze']:
                if m not in t.columns: t[m] = 0
            t = t[['Gold', 'Silber', 'Bronze']]
            t['Gesamt'] = t.sum(axis=1)
            t = t.sort_values(by=['Gold', 'Silber', 'Bronze'], ascending=False).reset_index()

            with t1:
                anzeige = t.copy()
                anzeige.columns = ['Land', '🥇', '🥈', '🥉', 'Gesamt']
                zeige_html_tabelle(anzeige)
            with t2:
                fig = px.pie(t.head(10), values='Gesamt', names='Team',
                             title=f"Medaillenverteilung in {sport_wahl}",
                             category_orders={"Team": t['Team'].tolist()})
                fig.update_traces(sort=False)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.subheader(f"Ergebnisse: {disziplin_wahl}")
        df_einzel = df_sport[df_sport["event_title"] == disziplin_wahl].copy()
        df_einzel['rank_sort'] = pd.to_numeric(df_einzel['rank_position'], errors='coerce')
        df_einzel = df_einzel.sort_values(by='rank_sort', na_position='last')
        df_einzel['Rang'] = df_einzel.apply(hole_rang_anzeige, axis=1)
        zeige_html_tabelle(df_einzel[['Rang', 'Name', 'Team']].rename(columns={'Name': 'Athlet', 'Team': 'Land'}))

def zeige_gesamt_medaillenspiegel(df_jahr, jahr):
    """ Zeigt den kompletten Medaillenspiegel des ausgewählten Jahres"""
    st.title(f"Medaillenspiegel {jahr}")
    df_m = df_jahr.dropna(subset=['Medal']).copy()
    if not df_m.empty:
        gt = df_m.pivot_table(index='Team', columns='Medal', aggfunc='size', fill_value=0)
        for m in ['Gold', 'Silber', 'Bronze']:
            if m not in gt.columns: gt[m] = 0
        gt = gt[['Gold', 'Silber', 'Bronze']]
        gt['Gesamt'] = gt.sum(axis=1)
        gt = gt.sort_values(by=['Gold', 'Silber', 'Bronze'], ascending=False).reset_index()
        gt.columns = ['Land', '🥇', '🥈', '🥉', 'Gesamt']
        zeige_html_tabelle(gt)

# 4. HAUPTSTEUERUNG
def main():
    benutzerdefiniertes_css()
    df = lade_daten()

    st.sidebar.header("Navigation")
    seite = st.sidebar.radio("Bereich wählen:", [
        "Disziplinanalyse", 
        "Gesamt Medaillenspiegel", 
        "Athletenprofil", 
        "Ewiger Medaillenspiegel",
        "Top Athleten"
    ])
    
    if seite == "Athletenprofil":
        zeige_athleten_profil(df)
    elif seite == "Ewiger Medaillenspiegel":
        zeige_ewigen_medaillenspiegel(df)
    elif seite == "Top Athleten":
        zeige_top_athleten(df)
    else:
        st.sidebar.divider()
        jahre = sorted(df["Year"].unique(), reverse=True)
        jahr_auswahl = st.sidebar.selectbox("Jahr auswählen:", options=jahre)
        df_jahr_gefiltert = df[df["Year"] == jahr_auswahl]

        if seite == "Disziplinanalyse":
            zeige_disziplin_analyse(df_jahr_gefiltert, jahr_auswahl)
        else:
            zeige_gesamt_medaillenspiegel(df_jahr_gefiltert, jahr_auswahl)

if __name__ == "__main__":
    main()