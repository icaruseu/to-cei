from model.charter import Charter

if __name__ == "__main__":
    print(
        Charter(
            "1307 II 22",
            abstract="Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.",
            abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
            issuer="Konrad von Lintz",
            recipient="Heinrich, des Praitenvelders Schreiber",
            transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
            issued_place="Wiener",
        ).to_string()
    )
