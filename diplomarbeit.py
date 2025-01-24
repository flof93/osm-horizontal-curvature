import curvy

coords={"Wien":(15, 48, 17, 49)} # Koordinaten Wiens
curvy = curvy.Curvy(*coords["Wien"], desired_railway_types=["tram"]) # Liest die Tramstrecken Wiens aus
curvy.download_track_data()
print(curvy)