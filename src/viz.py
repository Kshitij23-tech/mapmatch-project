import folium

ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/%s/MapServer/tile/{z}/{y}/{x}"


def _base(lat, lon, zoom):
    """Map with two background layers (street map and satellite). The OpenStreetMap tile server refuses pages opened from a file."""
    m = folium.Map(location=[lat, lon], zoom_start=zoom, tiles=None, max_zoom=19)
    folium.TileLayer(ESRI % "World_Street_Map", attr="Esri", name="street map", max_zoom=19).add_to(m)
    folium.TileLayer(ESRI % "World_Imagery", attr="Esri, Maxar, Earthstar Geographics", name="satellite", show=False, max_zoom=19).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    return m


COLOR = {0: "#e08a00", 1: "#0d8f8f", 2: "#6b7280", -1: "#000000"}   # main road, service road, other, no match


def _roads(m, edges):
    e = edges.to_crs(4326)[["geometry", "hw", "grp"]].copy()
    folium.GeoJson(e.to_json(), tooltip=folium.GeoJsonTooltip(fields=["hw", "grp"]),
                   style_function=lambda f: {"color": COLOR[int(f["properties"]["grp"])], "weight": 5, "opacity": 0.45}).add_to(m)


def trip_map(d, groups=None, edges=None, label_every=0):
    """Map of one trip. d needs lat and lon (and idx if label_every is used).
    groups = a colour code per point (0 main, 1 service, 2 other, -1 none) or None.
    label_every = write the point number on the map every N points."""
    m = _base(d["lat"].mean(), d["lon"].mean(), 16)
    if edges is not None:
        _roads(m, edges)
    idx = d["idx"].to_numpy() if "idx" in d else range(len(d))
    for i, (la, lo, k) in enumerate(zip(d["lat"], d["lon"], idx)):
        col = "#14213d" if groups is None else COLOR[int(groups[i])]
        folium.CircleMarker([la, lo], radius=3, color=col, fill=True, fill_opacity=0.9, tooltip=f"point {k}").add_to(m)
        if label_every and k % label_every == 0:
            folium.Marker([la, lo], icon=folium.DivIcon(
                html=f'<div style="font:bold 11px sans-serif;color:#b00020;background:#fff;padding:0 2px;border:1px solid #b00020">{k}</div>')).add_to(m)
    folium.Marker([d["lat"].iloc[0], d["lon"].iloc[0]], tooltip="start").add_to(m)
    return m


def roads_map(edges, df):
    """All roads (coloured by group) and all trips as dots."""
    m = _base(df["lat"].mean(), df["lon"].mean(), 12)
    _roads(m, edges)
    palette = ["#1d4ed8", "#be123c", "#15803d", "#7c3aed", "#b45309", "#0e7490"]
    for k, (tid, d) in enumerate(df.groupby("trip")):
        for la, lo in zip(d["lat"].to_numpy()[::5], d["lon"].to_numpy()[::5]):
            folium.CircleMarker([la, lo], radius=2, color=palette[k % len(palette)], fill=True, tooltip=tid).add_to(m)
    return m