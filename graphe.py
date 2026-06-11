import streamlit as st
import pandas as pd
import plotly.express as px
import chardet
import io

st.set_page_config(page_title="📊 Dashboard Auto", layout="wide")
st.title("📊 Dashboard Automatique")

fichier = st.file_uploader(
    "📁 Uploader un fichier CSV ou Excel",
    type=["csv", "xlsx"]
)

if fichier is not None:

    # ==========================
    # CHARGEMENT DU FICHIER
    # ==========================

    if fichier.name.endswith(".csv"):

        raw = fichier.read()

        result = chardet.detect(raw)
        encoding = result["encoding"] or "latin-1"

        sample = raw[:2000].decode(encoding, errors="replace")

        if sample.count(";") > sample.count(","):
            sep = ";"
        elif sample.count("\t") > sample.count(","):
            sep = "\t"
        else:
            sep = ","

        try:
            df = pd.read_csv(
                io.BytesIO(raw),
                encoding=encoding,
                sep=sep
            )

            st.success(
                f"✅ Encodage : {encoding} | Séparateur : '{sep}'"
            )

        except Exception as e:
            st.error(f"Erreur : {e}")
            st.stop()

    else:
        df = pd.read_excel(fichier)

    # ==========================
    # NETTOYAGE
    # ==========================

    df = df.drop_duplicates()
    df = df.dropna(how="all")

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # numériques
    numeric_cols = df.select_dtypes(include=["number"]).columns

    for col in numeric_cols:
        df[col] = df[col].fillna(df[col].mean())

    # qualitatives
    categorical_cols = df.select_dtypes(exclude=["number"]).columns

    for col in categorical_cols:
        if not df[col].mode().empty:
            df[col] = df[col].fillna(df[col].mode()[0])

    # dates
    for col in df.columns:
        if df[col].dtype == "object":
            try:
                df[col] = pd.to_datetime(df[col])
            except:
                pass

    # ==========================
    # TYPES DES VARIABLES
    # ==========================

    def get_type(col):

        if pd.api.types.is_datetime64_any_dtype(df[col]):
            return "📅 Date"

        elif pd.api.types.is_numeric_dtype(df[col]):
            return "🔢 Quantitative"

        else:
            return "🔤 Qualitative"

    types = {col: get_type(col) for col in df.columns}

    # ==========================
    # APERÇU
    # ==========================

    with st.expander("📋 Aperçu des données"):

        st.dataframe(df)

        type_df = pd.DataFrame({
            "Colonne": list(types.keys()),
            "Type": list(types.values())
        })

        st.dataframe(type_df)

    st.markdown("---")

    # ==========================
    # VARIABLES
    # ==========================

    st.subheader("🎯 Sélection")

    col1, col2 = st.columns(2)

    with col1:

        x_col = st.selectbox(
            "Variable X",
            df.columns,
            format_func=lambda c: f"{c} ({types[c]})"
        )

    with col2:

        y_options = ["Aucune"] + [
            c for c in df.columns if c != x_col
        ]

        y_col = st.selectbox(
            "Variable Y",
            y_options
        )

    # ==========================
    # CHOIX AUTO DU GRAPHE
    # ==========================

    def meilleur_graphe(x, y):

        tx = types[x]

        if y == "Aucune":

            if tx == "🔢 Quantitative":
                return "Histogramme"

            elif tx == "🔤 Qualitative":
                return "Bar chart"

            else:
                return "Line chart"

        ty = types[y]

        if tx == "📅 Date" or ty == "📅 Date":
            return "Line chart"

        elif (
            tx == "🔢 Quantitative"
            and ty == "🔢 Quantitative"
        ):
            return "Scatter plot"

        elif (
            tx == "🔤 Qualitative"
            and ty == "🔢 Quantitative"
        ):
            return "Boxplot"

        elif (
            tx == "🔢 Quantitative"
            and ty == "🔤 Qualitative"
        ):
            return "Boxplot"

        return "Bar chart"

    graphe_auto = meilleur_graphe(
        x_col,
        y_col
    )

    options = [
        "Histogramme",
        "Bar chart",
        "Scatter plot",
        "Boxplot",
        "Line chart",
        "Pie chart"
    ]

    st.info(
        f"💡 Graphique recommandé : {graphe_auto}"
    )

    graphe = st.selectbox(
        "Type de graphique",
        options,
        index=options.index(graphe_auto)
    )

    st.markdown("---")

    # ==========================
    # FILTRE
    # ==========================

    st.subheader("🔍 Filtre")

    filtre_col = st.selectbox(
        "Filtrer par",
        df.columns
    )

    df_filtre = df.copy()

    if types[filtre_col] == "🔤 Qualitative":

        valeurs = df[filtre_col].dropna().unique()

        choix = st.multiselect(
            "Valeurs",
            valeurs,
            default=valeurs
        )

        df_filtre = df[
            df[filtre_col].isin(choix)
        ]

    elif types[filtre_col] == "🔢 Quantitative":

        min_v = float(df[filtre_col].min())
        max_v = float(df[filtre_col].max())

        plage = st.slider(
            "Plage",
            min_v,
            max_v,
            (min_v, max_v)
        )

        df_filtre = df[
            (df[filtre_col] >= plage[0])
            &
            (df[filtre_col] <= plage[1])
        ]

    # ==========================
    # GRAPHIQUE
    # ==========================

    st.subheader("📈 Visualisation")

    titre = f"{graphe} - {x_col}"

    fig = None

    try:

        if graphe == "Histogramme":

            fig = px.histogram(
                df_filtre,
                x=x_col,
                title=titre
            )

        elif graphe == "Bar chart":

            if y_col != "Aucune":

                fig = px.bar(
                    df_filtre,
                    x=x_col,
                    y=y_col,
                    title=titre
                )

            else:

                counts = (
                    df_filtre[x_col]
                    .value_counts()
                    .reset_index()
                )

                counts.columns = [x_col, "count"]

                fig = px.bar(
                    counts,
                    x=x_col,
                    y="count",
                    title=titre
                )

        elif graphe == "Scatter plot":

            if y_col != "Aucune":

                fig = px.scatter(
                    df_filtre,
                    x=x_col,
                    y=y_col,
                    title=titre
                )

        elif graphe == "Boxplot":

            if y_col != "Aucune":

                fig = px.box(
                    df_filtre,
                    x=x_col,
                    y=y_col,
                    title=titre
                )

        elif graphe == "Line chart":

            if y_col != "Aucune":

                fig = px.line(
                    df_filtre,
                    x=x_col,
                    y=y_col,
                    title=titre
                )

        elif graphe == "Pie chart":

            counts = (
                df_filtre[x_col]
                .value_counts()
                .reset_index()
            )

            counts.columns = [x_col, "count"]

            fig = px.pie(
                counts,
                names=x_col,
                values="count",
                title=titre
            )

        if fig is not None:
            st.plotly_chart(
                fig,
                use_container_width=True
            )

    except Exception as e:
        st.error(str(e))

    # ==========================
    # EXPORT CSV
    # ==========================

    csv = df_filtre.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        "⬇️ Télécharger CSV",
        data=csv,
        file_name="donnees_filtrees.csv",
        mime="text/csv"
    )
