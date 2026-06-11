import streamlit as st
import pandas as pd
import plotly.express as px
import chardet
import io
st.set_page_config(page_title="📊 Dashboard Auto", layout="wide")
st.title("📊 Dashboard Automatique")

# ══════════════════════════════════════
# UPLOAD & CHARGEMENT
# ══════════════════════════════════════
fichier = st.file_uploader("📁 Uploader un fichier CSV ou Excel", type=["csv", "xlsx","json"])

if fichier is not None:

    if fichier.name.endswith(".csv"):
      raw = fichier.read()

    # 1 — Encodage
      result = chardet.detect(raw)
      encoding = result["encoding"] or "latin-1"

    # 2 — Séparateur
      sample = raw[:2000].decode(encoding, errors="replace")
      if sample.count(";") > sample.count(","):
        sep = ";"
      elif sample.count("\t") > sample.count(","):
        sep = "\t"
      else:
        sep = ","

    # 3 — Chargement
      try:
        df = pd.read_csv(io.BytesIO(raw), encoding=encoding, sep=sep)
        st.success(f"✅ Fichier lu — encodage: {encoding} | séparateur: '{sep}'")
      except Exception as e:
        st.error(f"❌ Erreur : {e}")
        st.stop()
    else :
        df = pd.read_excel(fichier)

    # ══════════════════════════════════════
    # NETTOYAGE AUTOMATIQUE
    # ══════════════════════════════════════
    df = df.drop_duplicates()
    df = df.dropna(how="all")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    numeric_cols = df.select_dtypes(include=['number']).columns

for col in numeric_cols:
    df[col] = df[col].fillna(df[col].mean())
categorical_cols = df.select_dtypes(exclude=['number']).columns

for col in categorical_cols:
    if not df[col].mode().empty:
        df[col] = df[col].fillna(df[col].mode()[0])
st.write(df.dtypes)

    # Détecter les colonnes dates
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass

    # ══════════════════════════════════════
    # CLASSIFIER LES COLONNES
    # ══════════════════════════════════════
    def get_type(col):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return "📅 Date"
        elif pd.api.types.is_numeric_dtype(df[col]):
            return "🔢 Quantitative"
        else:
            return "🔤 Qualitative"

    types = {col: get_type(col) for col in df.columns}

    # ══════════════════════════════════════
    # APERÇU DES DONNÉES
    # ══════════════════════════════════════
    with st.expander("📋 Aperçu des données nettoyées"):
        st.dataframe(df)
        st.write("**Types détectés :**")
        type_df = pd.DataFrame({"Colonne": types.keys(), "Type": types.values()})
        st.dataframe(type_df)

    st.markdown("---")

    # ══════════════════════════════════════
    # SÉLECTION X ET Y
    # ══════════════════════════════════════
    st.subheader("🎯 Sélection des variables")

    col1, col2 = st.columns(2)

    with col1:
        x_col = st.selectbox(
            "Variable X :",
            options=df.columns,
            format_func=lambda c: f"{c}  ({types[c]})"
        )

    with col2:
        y_options = ["Aucune"] + [c for c in df.columns if c != x_col]
        y_col = st.selectbox(
            "Variable Y (optionnelle) :",
            options=y_options,
            format_func=lambda c: f"{c}  ({types[c]})" if c != "Aucune" else "Aucune"
        )

    # ══════════════════════════════════════
    # DÉTECTION DU MEILLEUR GRAPHIQUE
    # ══════════════════════════════════════
    def meilleur_graphe(x, y):
        tx = types[x]
        if y == "Aucune":
            if tx == "🔢 Quantitative":
                return "Histogramme"
            elif tx == "🔤 Qualitative":
                return "Bar chart"
            elif tx == "📅 Date":
                return "Line chart"
        else:
            ty = types[y]
            if tx == "📅 Date" or ty == "📅 Date":
                return "Line chart"
            elif tx == "🔢 Quantitative" and ty == "🔢 Quantitative":
                return "Scatter plot"
            elif tx == "🔤 Qualitative" and ty == "🔢 Quantitative":
                return "Boxplot"
            elif tx == "🔢 Quantitative" and ty == "🔤 Qualitative":
                return "Boxplot"
            elif tx == "🔤 Qualitative" and ty == "🔤 Qualitative":
                return "Bar chart"
        return "Bar chart"

    graphe_auto = meilleur_graphe(x_col, y_col)

    # Choix manuel ou automatique
    graphe_options = ["Histogramme", "Bar chart", "Scatter plot", "Boxplot", "Line chart", "Pie chart"]

    col3, col4 = st.columns(2)
    with col3:
        st.info(f"💡 Graphique recommandé : **{graphe_auto}**")
    with col4:
        graphe_choix = st.selectbox("Ou choisir manuellement :", graphe_options, index=graphe_options.index(graphe_auto))

    st.markdown("---")

    # ══════════════════════════════════════
    # FILTRE SIMPLE
    # ══════════════════════════════════════
    st.subheader("🔍 Filtre")

    col_filtre = st.selectbox("Filtrer par :", df.columns, format_func=lambda c: f"{c}  ({types[c]})")

    if types[col_filtre] == "🔤 Qualitative":
        valeurs = df[col_filtre].unique()
        choix = st.multiselect("Valeurs :", valeurs, default=list(valeurs))
        df_filtre = df[df[col_filtre].isin(choix)]

    elif types[col_filtre] == "🔢 Quantitative":
        min_v = float(df[col_filtre].min())
        max_v = float(df[col_filtre].max())
        plage = st.slider("Plage :", min_v, max_v, (min_v, max_v))
        df_filtre = df[(df[col_filtre] >= plage[0]) & (df[col_filtre] <= plage[1])]

    else:
        df_filtre = df.copy()

    st.write(f"**{df_filtre.shape[0]} lignes** après filtrage")

    st.markdown("---")

    # ══════════════════════════════════════
    # GÉNÉRATION DU GRAPHIQUE
    # ══════════════════════════════════════
    st.subheader("📈 Visualisation")

    titre = f"{graphe_choix} — {x_col}" + (f" vs {y_col}" if y_col != "Aucune" else "")

    fig = None

    try:
        if graphe_choix == "Histogramme":
            fig = px.histogram(df_filtre, x=x_col, title=titre, color_discrete_sequence=["#636EFA"])

        elif graphe_choix == "Bar chart":
            if y_col != "Aucune":
                fig = px.bar(df_filtre, x=x_col, y=y_col, title=titre)
            else:
                counts = df_filtre[x_col].value_counts().reset_index()
                counts.columns = [x_col, "count"]
                fig = px.bar(counts, x=x_col, y="count", title=titre)

        elif graphe_choix == "Scatter plot":
            if y_col != "Aucune":
                fig = px.scatter(df_filtre, x=x_col, y=y_col, title=titre, trendline="ols")
            else:
                st.warning("Scatter plot nécessite une variable Y.")

        elif graphe_choix == "Boxplot":
            if y_col != "Aucune":
                fig = px.box(df_filtre, x=x_col, y=y_col, title=titre)
            else:
                fig = px.box(df_filtre, y=x_col, title=titre)

        elif graphe_choix == "Line chart":
            if y_col != "Aucune":
                fig = px.line(df_filtre.sort_values(x_col), x=x_col, y=y_col, title=titre)
            else:
                st.warning("Line chart nécessite une variable Y.")

        elif graphe_choix == "Pie chart":
            counts = df_filtre[x_col].value_counts().reset_index()
            counts.columns = [x_col, "count"]
            fig = px.pie(counts, names=x_col, values="count", title=titre)

        if fig:
            fig.update_layout(title_font_size=20, height=500)
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"Erreur lors de la génération du graphique : {e}")

    # ══════════════════════════════════════
    # TÉLÉCHARGEMENT
    # ══════════════════════════════════════
    st.markdown("---")
    csv = df_filtre.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Télécharger les données filtrées", data=csv, file_name="données_filtrées.csv", mime="text/csv")
