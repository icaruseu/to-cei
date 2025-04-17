import pytest
from lxml import etree


@pytest.fixture
def valid_cei():
    return etree.fromstring(
        """<cei:text xmlns:cei="http://www.monasterium.net/NS/cei" b_name="Schotten, OSB" id="217593" n="Schotten, OSB$103" type="charter">
	<cei:front>
	   <cei:sourceDesc>
		  <cei:sourceDescVolltext>
			 <cei:bibl>HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123-124</cei:bibl>
		  </cei:sourceDescVolltext>
		  <cei:sourceDescRegest>
			 <cei:bibl>HAUSWIRTH, Schotten (=FRA II/18, 1859) S. 123, Nr. 103</cei:bibl>
		  </cei:sourceDescRegest>
	   </cei:sourceDesc>
	</cei:front>
	<cei:body>
	   <cei:idno id="1307_II_22.1">1307 II 22</cei:idno>
	   <cei:chDesc>
		  <cei:abstract>Konrad von Lintz, Caplan zu St. Pankraz, beurkundet den vorstehenden Vertrag mit Heinrich, des Praitenvelders Schreiber.</cei:abstract>
		  <cei:issued>
			 <cei:placeName>Wien</cei:placeName>
			 <cei:dateRange from="13070222" to="13070222">1307 Februar 22</cei:dateRange>
		  </cei:issued>
		  <cei:witnessOrig>
			 <cei:traditioForm>orig.</cei:traditioForm>
			 <cei:figure n="StAS__13070222-2">
				<cei:graphic url="K.._MOM-Bilddateien._~Schottenjpgweb._~StAS__13070222-2.jpg">StAS__13070222-2.jpg</cei:graphic>
			 </cei:figure>
			 <cei:archIdentifier>
				<cei:arch>Stiftsarchiv Schotten, Wien (http://www.schottenstift.at)</cei:arch>
                <cei:altIdentifier type="old">217593</cei:altIdentifier>
			 </cei:archIdentifier>
			 <cei:physicalDesc>
				<cei:material>Pergament</cei:material>
			 </cei:physicalDesc>
			 <cei:auth>
				<cei:sealDesc>                  2 Siegel                </cei:sealDesc>
			 </cei:auth>
		  </cei:witnessOrig>
		  <cei:witListPar></cei:witListPar>
		  <cei:diplomaticAnalysis>
			 <cei:quoteOriginaldatierung>an sand peters tage in der vasten, als er avf den stvl ze Rome gesatz wart</cei:quoteOriginaldatierung>
		  </cei:diplomaticAnalysis>
		  <cei:lang_MOM>Deutsch</cei:lang_MOM>
	   </cei:chDesc>
	   <cei:tenor>Ich Chvnrad von Lintz, zv den zeiten Schreiber des Hohen fvrsten Herzogen Fridriches von Osterreiche vnd Chapplan vnd verweser der Chappellen sand Pangratien, die da leit avf des Herzogen hove ze Wienne, vergihe vnd tvn chvnt allen den, die disen prief lesent oder horent lesen, die nv lebent vnd hernah chvnftich sint, daz ich der vorgenanten Chappellen sand Pangratien vnd mir gechavft han wider Hainrichen des praitenvelder Schreiber vnd seine havsvrowen vron Gerdravden ain phvnt wienner phenninge geltes pvrchrehtes avf ir gemavrten Havse, daz da leit hinder der vorgenanten Chappellen sand Pangratien, vmb zehen phvnt wienner phenninge, der ich sie reht vnd redlichen gewert han, also mit avzgenomner rede, swanne daz ist, daz Hainrich der Schreiber vnd sein havsvrowe vro Gerdravt oder ir erben, ob sie niht ensint, mir Chvnraden oder deme, der der vorgenanten Chappellen sand Pangracien Chapplan ist, vnd avch derselben Chappellen gebent ain ander phvnt Wienner phenninge geltes pvrchrehtes innerhalben der Ringmavre ze wienne, daz ir also maezzich ist, als daz phvnt geltes avf ir havse, so svln sie vnd ir Havs fvrbaz des phvndes geltes ledich sein, vnd sol avch ich Chvnrat, oder swer der vorgenanten Chappellen sand Pangratien Chapplan ist, in iren prief an alle  Widerrede wider geben. Die weile aber des niht geschiht, so sol Hainrich der Schreiber vnd sein havsvrowe vro Gerdravt, oder swer daz vorgenant ir gemavrtes Havs nah in besitzzet, daz vorgesprochen phvnt geltes purchrehtes von demselben havse dienen mir Chvnraden von Lintz oder deme, der der vorgenanten Chappellen Chapplan ist, vnd avch derselben Chappellen sand Pangratien ze drien zeiten in dem Jare, achzich phenninge an sand Jorgen tage, achzich phenninge an sand Michels tage vnd achzich phenninge ze weihenahten mit allem dem reht, als man an der pvrchreht hie ze Wienne dienet, vnd gib in darvber disen prief ze ainem vrchvnde vnd ze ainem gezevge diser sache versigilten mit meinem Insigil vnd mit hern Helmwiges Insigil, der zu den zeiten verweser was der chirchen sand Michels ze Wienne, der diser sache gezevg ist mit seinem Insigil, vnd sint avch des gezevg her Gerhart, her Dietrich, her Hainrich vnd her Perhtram die priester, her Chvnrat der Witzze, Starchant der Schoberl, Seibot der Heftler, maister Vlrich der pogner, Elbel der pogner sein gesweie, Hainrich daz Vmbilde, Ludweig der Schilter, Johan der Gokler vnd ander frvme levte genvch, den dise sache wol chvnt ist. Diser prief ist geben ze Wienne, do von Christes gebvrt waren ergangen Drevzehen Hvndert iar in dem Sibenten Jare darnah, an sand peters tage in der vasten, als er avf den stvl ze Rome gesatz wart.</cei:tenor>
	</cei:body>
	<cei:back>
	   <cei:persName reg="Konrad von Linz, Schreiber, Kaplan der Kapelle St. Pankraz, Aussteller">Chvnrad von Lintz</cei:persName>
	   <cei:placeName reg="Wien" type="Ortsindex">wienne</cei:placeName>
	   <cei:persName reg="Heinrich, Schreiber des Breitenfelder">Hainrichen des praitenvelder Schreiber</cei:persName>
	   <cei:divNotes></cei:divNotes>
	</cei:back>
 </cei:text>"""
    )


@pytest.fixture
def invalid_cei():
    return etree.fromstring("<notCei>This is not valid CEI</notCei>")
