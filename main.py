from model.charter import Charter

if __name__ == "__main__":
    print(
        Charter(
            "1307 II 22",
            abstract="Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.",
            abstract_bibls=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
            archive="Stiftsarchiv Schotten, Wien (http://www.schottenstift.at)",
            chancellary_remarks=[
                "commissio domini imperatoris in consilio",
                "Jüngerer Dorsualvermerk mit Regest",
            ],
            condition="Beschädigtes Pergament",
            date="1307 II 22",
            date_quote="an sand peters tage in der vasten, als er avf den stvl ze Rome gesatz wart",
            date_value="13070222",
            dimensions="20x20cm",
            external_link="https://example.com/charters/1",
            graphic_urls=[
                "K.._MOM-Bilddateien._~Schottenjpgweb._~StAS__13070222-2.jpg"
            ],
            issued_place="Wiener Neustadt",
            issuer="Konrad von Lintz",
            language="Deutsch",
            material="Pergament",
            notarial_authentication="Albertus Magnus",
            recipient="Heinrich, des Praitenvelders Schreiber",
            seals="2 Siegel",
            tradition="orig.",
            transcription="Ich Hainrich, des Praitenvelder Schreiber, [...] ze Rome gesatz wart.",
            transcription_bibls="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
        ).to_string()
    )
