# =================================================================
# 🟧 ONGLET 7 — CC PYRENEES AUDOISES
# =================================================================

with tab7:
    st.header("🐄 CC Pyrénées Audoises")
    df_communes_met_cc = df_communes_occitanie[df_communes_occitanie['epci_nom'] == 'CC Pyrénées Audoises']
    print('Population de la CC Pyrénées Audoises :', df_communes_met_cc['population'].sum())



    # --- KPI ---
    total_etabs = df_cc['numero_finess_etablissement'].nunique()
    nb_types = df_cc['type d etablissements'].nunique()
    nb_communes = df_communes_met_cc['nom_standard'].nunique()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Établissements recensés", f"{total_etabs}")
    col2.metric("Types d’établissements", f"{nb_types}")
    col3.metric("Communes couvertes", f"{nb_communes}")
    col4.metric("Nb de personnes par établissement", f"{df_communes_met_cc['population'].sum()/df_cc['numero_finess_etablissement'].nunique(): .0f}")

    st.subheader("Typologie des établissements de la CC Pyrénées Audoises")

    table_typo_cc = (
        df_cc.groupby('type d etablissements')
          .agg(nb_etablissements=('numero_finess_etablissement', 'count'))
          .reset_index()
    )
    table_typo_cc['pourcentage'] = (table_typo_cc['nb_etablissements'] / total_etabs * 100).round(2)
    table_typo_cc = table_typo_cc.sort_values('nb_etablissements', ascending=False)

    st.dataframe(table_typo_cc, use_container_width=True, hide_index=True)

    fig_typo = px.bar(
        table_typo_cc,
        x='type d etablissements',
        y='nb_etablissements',
        title="Nombre d'établissements par typologie",
        labels={'type d etablissements': 'Typologie', 'nb_etablissements': 'Nombre'},
    )
    st.plotly_chart(fig_typo, use_container_width=True)
    # --- Carte interactive des établissements de CC Pyrénees  ---

    groupes_cc = sorted(df_cc['type d etablissements'].dropna().unique())
    communes_cc = sorted(df_cc['nom_standard'].dropna().unique())

    option_tous_groupes_cc = "Tous les types"
    option_toutes_communes_cc = "Toutes les communes"

    selection_groupes = st.multiselect(
        "Sélectionner un ou plusieurs types d'établissements :",
        [option_tous_groupes_cc] + groupes_cc,
        default=[option_tous_groupes_cc],
        key="filtre_groupes_cc"
    )

    selection_communes = st.multiselect(
        "Sélectionner une ou plusieurs communes :",
        [option_toutes_communes_cc] + communes_cc,
        default=[option_toutes_communes_cc],
        key="filtre_communes_cc"
    )

    df_filtre_cc = df_cc.copy()

    if option_tous_groupes_cc not in selection_groupes:
        df_filtre_cc = df_filtre_cc[df_filtre_cc['type d etablissements'].isin(selection_groupes)]

    if option_toutes_communes_cc not in selection_communes:
        df_filtre_cc = df_filtre_cc[df_filtre_cc['nom_standard'].isin(selection_communes)]

      # Centre de la carte sur CC 
    center_lat = 42.8777068
    center_lon = 2.1847657
    zoom_level = 10   # 👉 Ajuste ici (12 = ville, 13 = centre, 14 = rues)

    fig = px.scatter_mapbox(
        df_filtre_cc,
        lat="latitude",
        lon="longitude",
        hover_name="raison_sociale",
        hover_data={"type d etablissements": True},
        color="type d etablissements",
        size_max=30, #taille max des points
        zoom=zoom_level,        # 👉 Utilisation du zoom dynamique
        height=650
    )

    fig.update_layout(
        mapbox_style="open-street-map",
        mapbox_center={"lat": center_lat, "lon": center_lon},  # 👉 Centre réel
        margin={"r":0, "t":0, "l":0, "b":0}
    )
    fig.update_traces(
    marker={'size': 18}   # 👉 taille des ronds (augmente si tu veux)
    )

    st.plotly_chart(fig, use_container_width=True)
