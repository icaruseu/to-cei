from astropy.time.core import Time

from model.charter import Charter

if __name__ == "__main__":
    print(
        Charter(
            "1307 II 22",
            abstract="Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.",
            abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
            date="1307 II 22",
            date_value="13070222",
            issued_place="Wiener",
            issuer="Konrad von Lintz",
            recipient="Heinrich, des Praitenvelders Schreiber",
            tradition_form="orig.",
            transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
        ).to_string()
    )
