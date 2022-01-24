from model.charter import Charter

if __name__ == "__main__":
    print(
        Charter(
            "1307 II 22",
            abstract="Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.",
            abstract_sources=["HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103"],
            archive="Stiftsarchiv Schotten, Wien (http://www.schottenstift.at)",
            chancellary_remarks=[
                "commissio domini imperatoris in consilio",
                "Jüngerer Dorsualvermerk mit Regest",
            ],
            comments="The diplomatic analysis is inconclusive",
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
            literature="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103",
            literature_abstracts="[RI XIII] H. 4 n. 778, in: Regesta Imperii Online, URI: http://www.regesta-imperii.de/id/1477-04-02_1_0_13_4_0_10350_778 (Abgerufen am 13.11.2016)",
            literature_depictions="ADEVA-Verlag, Die Ostarrichi-Urkunde – Luxus-Ausgabe. Ausstattung und Preise, In: ADEVA Home (2012), online unter <http://www.adeva.com/faks_detail_bibl.asp?id=127> (12.12.2012)",
            literature_editions=[
                "Urkunden der burgundischen Rudolfinger, ed. Theodor Schieffer, Monumenta Germaniae Historica, Diplomata, 2A, Regum Burgundiae e stirpe Rudolfina diplomata et acta, München 1977; in der Folge: MGH DD Burg. 103."
            ],
            literature_secondary=[
                "HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
                "HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 127, Nr. 105",
            ],
            material="Pergament",
            notarial_authentication="Albertus Magnus",
            recipient="Heinrich, des Praitenvelders Schreiber",
            seals="2 Siegel",
            tradition="orig.",
            transcription="Ich Hainrich, des Praitenvelder Schreiber, [...] ze Rome gesatz wart.",
            transcription_sources="HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124",
        ).to_string()
    )
