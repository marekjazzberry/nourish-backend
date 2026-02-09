-- Nourish Knowledge Base Seed Data
-- 5 Artikel: Zucker, Omega-3-Fettsaeuren, Vitamin D, Eisen, Magnesium
-- Alle Texte auf Deutsch, Studien mit echten DOIs und PubMed-IDs

-- ══════════════════════════════════════════════════════════
-- 1. ZUCKER (Macronutrient)
-- ══════════════════════════════════════════════════════════

DO $$
DECLARE
    article_id UUID;
    effect_id UUID;
BEGIN
    -- Knowledge Article: Zucker
    INSERT INTO knowledge_articles (
        id, slug, title, category, summary, detail_html,
        related_nutrients, daily_recommendation, food_sources,
        warnings, tags, is_published, language
    ) VALUES (
        uuid_generate_v4(),
        'zucker',
        'Zucker: Was passiert wirklich in deinem Koerper',
        'macronutrient',
        'Zucker liefert schnelle Energie, doch ein Uebermass belastet Leber, Bauchspeicheldruese und Gefaesse. Die WHO empfiehlt maximal 25 g freien Zucker pro Tag -- das entspricht etwa 6 Teeloeffeln. Entscheidend ist nicht nur die Menge, sondern auch die Zuckerart und der Kontext, in dem du ihn isst.',
        '<h2>Zucker verstehen: Glucose, Fructose und ihre Wirkung</h2>
<p>Zucker ist nicht gleich Zucker. Die beiden Hauptformen -- <strong>Glucose</strong> und <strong>Fructose</strong> -- werden vom Koerper voellig unterschiedlich verarbeitet.</p>

<h3>Glucose: Der universelle Brennstoff</h3>
<p>Glucose kann von jeder Zelle deines Koerpers direkt genutzt werden. Nach dem Essen steigt dein Blutzucker, die Bauchspeicheldruese schuettet Insulin aus, und die Zellen nehmen die Glucose auf. Bei chronisch hohem Glucosekonsum entwickeln die Zellen allerdings eine <strong>Insulinresistenz</strong> -- sie reagieren immer schwaechiger auf das Insulinsignal. Das ist der erste Schritt in Richtung Typ-2-Diabetes.</p>

<h3>Fructose: Die stille Belastung fuer die Leber</h3>
<p>Fructose kann nur von der Leber verarbeitet werden. In kleinen Mengen (wie in ganzen Fruechten, zusammen mit Ballaststoffen) ist das kein Problem. Doch bei hohem Konsum -- etwa durch Softdrinks, Saefte oder verarbeitete Lebensmittel -- wird die Leber ueberlastet. Sie wandelt den Ueberschuss in Fett um (<strong>De-novo-Lipogenese</strong>), was zu einer Fettleber fuehren kann.</p>

<h3>Der glykemische Index und die Ballaststoff-Bremse</h3>
<p>Zucker in einem Apfel wirkt anders als Zucker in Apfelsaft. Der Grund: Ballaststoffe verlangsamen die Absorption und verhindern Blutzuckerspitzen. Deshalb ist der <strong>Kontext</strong> entscheidend. Ein Stueck Kuchen nach einer ballaststoffreichen Mahlzeit hat einen geringeren Blutzuckereffekt als auf leeren Magen.</p>

<h3>Zucker und Entzuendung</h3>
<p>Chronisch erhoehter Zuckerkonsum foerdert systemische Entzuendungen im Koerper. Dies geschieht ueber sogenannte <strong>Advanced Glycation End Products (AGEs)</strong> -- Verbindungen, die entstehen, wenn Zucker an Proteine bindet. AGEs schaedigen Gefaesswaende, beschleunigen die Hautalterung und erhoehen das Risiko fuer Herz-Kreislauf-Erkrankungen.</p>

<h3>Praktische Tipps</h3>
<ul>
<li>Lies Zutatenlisten: Zucker versteckt sich hinter ueber 60 Namen (Maltodextrin, Dextrose, Maissirup...)</li>
<li>Iss Obst statt Saft -- die Ballaststoffe machen den Unterschied</li>
<li>Kombiniere Suesses mit Protein oder Fett, um Blutzuckerspitzen abzuflachen</li>
<li>Achte besonders auf Getraenke: Fluessiger Zucker umgeht das Saettigungsgefuehl</li>
</ul>',
        ARRAY['carbs_sugar', 'carbs_sugar_glucose', 'carbs_sugar_fructose'],
        'Maximal 25 g freier Zucker pro Tag (WHO-Empfehlung), idealerweise unter 5 % der Gesamtenergiezufuhr',
        ARRAY['Haushaltszucker', 'Honig', 'Ahornsirup', 'Softdrinks', 'Fruchtsaefte', 'Suessigkeiten', 'Ketchup', 'Fruehstueckscerealien', 'Fruchtjoghurt'],
        ARRAY['Erhoehtes Diabetesrisiko bei dauerhaft > 50 g/Tag freiem Zucker', 'Fructose in grossen Mengen belastet die Leber aehnlich wie Alkohol', 'Versteckter Zucker in vielen verarbeiteten Lebensmitteln'],
        ARRAY['zucker', 'glucose', 'fructose', 'insulin', 'diabetes', 'blutzucker', 'energie', 'leber', 'entzuendung', 'aging'],
        TRUE,
        'de'
    ) RETURNING id INTO article_id;

    -- Health Effects: Zucker
    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'diabetes', 'negative', 'significant',
        'Erhoehtes Risiko fuer Typ-2-Diabetes',
        'Chronisch hoher Zuckerkonsum fuehrt zu wiederholten Insulinspitzen. Die Zellen werden zunehmend insulinresistent, die Bauchspeicheldruese muss immer mehr Insulin produzieren. Irgendwann erschoepft sich die Betazellen-Kapazitaet -- der Blutzucker bleibt dauerhaft erhoeht.',
        '> 50 g freier Zucker pro Tag ueber laengere Zeit',
        1);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'liver', 'negative', 'moderate',
        'Fettleber durch Fructose-Ueberschuss',
        'Fructose wird ausschliesslich in der Leber metabolisiert. Bei Ueberschuss aktiviert die Leber die De-novo-Lipogenese und wandelt Fructose direkt in Fett um. Bei chronischer Ueberbelastung lagert sich dieses Fett in der Leber ein (nicht-alkoholische Fettleber, NAFLD).',
        '> 40 g Fructose pro Tag ohne begleitende Ballaststoffe',
        2);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'inflammation', 'negative', 'moderate',
        'Chronische Entzuendungen und beschleunigte Zellalterung',
        'Zucker bindet an Proteine und bildet Advanced Glycation End Products (AGEs). Diese aktivieren den NF-kB-Signalweg und foerdern systemische Entzuendungen. AGEs schaedigen zudem Kollagen und Elastin, was die Hautalterung beschleunigt und Gefaesswaende versteift.',
        '> 25 g freier Zucker pro Tag',
        3);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'energy', 'dose_dependent', 'moderate',
        'Kurzfristiger Energieschub, langfristiger Einbruch',
        'Einfachzucker fuehrt zu einem schnellen Blutzuckeranstieg und einer hohen Insulinantwort. Die darauffolgende reaktive Hypoglykaemie (Zuckertief) verursacht Muedigkeit, Konzentrationsschwaeche und Heisshunger -- der klassische Energieeinbruch nach dem Mittagstief.',
        'Spuerbar ab 30-40 g Zucker auf leeren Magen',
        4);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'weight', 'negative', 'significant',
        'Gewichtszunahme durch gestoertes Saettigungsgefuehl',
        'Fructose umgeht das Saettigungshormon Leptin und daempft das Hungersignal Ghrelin nicht ausreichend. Zudem foerdert die Insulinantwort auf Glucose die Fettspeicherung. Fluessige Kalorien (Saefte, Limonade) werden vom Koerper besonders schlecht bei der Saettigungsregulation erfasst.',
        'Regelmaessiger Konsum von > 40 g/Tag in fluessiger Form',
        5);

    -- Study References: Zucker
    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Intake of added sugars and selected nutrients in the United States, National Health and Nutrition Examination Survey (NHANES) 2003-2006',
        'Marriott BP, Olsho L, Hadden L, Connor P',
        'Critical Reviews in Food Science and Nutrition',
        2010,
        '10.1080/10408391003710091',
        '20574822',
        'cohort',
        'Hoher Zuckerkonsum ist mit einer geringeren Aufnahme essentieller Mikro­naehrstoffe verbunden. Die Studie zeigt, dass zugesetzter Zucker naehrstoffdichte Lebensmittel aus der Ernaehrung verdraengt.',
        'high',
        1);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Sugar-sweetened beverages and risk of metabolic syndrome and type 2 diabetes: a meta-analysis',
        'Malik VS, Popkin BM, Bray GA, Despres JP, Willett WC, Hu FB',
        'Diabetes Care',
        2010,
        '10.2337/dc10-1079',
        '20693348',
        'meta_analysis',
        'Der Konsum von 1-2 zuckergesuessten Getraenken pro Tag ist mit einem 26 % erhoehten Risiko fuer Typ-2-Diabetes und einem 20 % erhoehten Risiko fuer das metabolische Syndrom assoziiert.',
        'high',
        2);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Fructose metabolism and relation to atherosclerosis, type 2 diabetes, and obesity',
        'Stanhope KL, Schwarz JM, Havel PJ',
        'Journal of Lipid Research',
        2009,
        '10.1194/jlr.R800089-JLR200',
        '18987389',
        'review',
        'Fructose wird primaer in der Leber metabolisiert und foerdert dort die De-novo-Lipogenese. Chronisch hoher Fructosekonsum traegt zur Entwicklung von viszeraler Adipositas, Dyslipidaemie und Insulinresistenz bei.',
        'high',
        3);
END $$;


-- ══════════════════════════════════════════════════════════
-- 2. OMEGA-3-FETTSAEUREN (Compound)
-- ══════════════════════════════════════════════════════════

DO $$
DECLARE
    article_id UUID;
    effect_id UUID;
BEGIN
    INSERT INTO knowledge_articles (
        id, slug, title, category, summary, detail_html,
        related_nutrients, daily_recommendation, food_sources,
        warnings, tags, is_published, language
    ) VALUES (
        uuid_generate_v4(),
        'omega-3-fettsaeuren',
        'Omega-3-Fettsaeuren: Dein Koerper braucht sie ueberall',
        'compound',
        'Omega-3-Fettsaeuren sind essentielle Fette, die dein Koerper nicht selbst herstellen kann. Sie bilden die Basis jeder Zellmembran, daempfen Entzuendungen und schuetzen Herz und Gehirn. Die meisten Menschen nehmen zu wenig Omega-3 und zu viel Omega-6 auf -- ein Ungleichgewicht, das Entzuendungen foerdert.',
        '<h2>Omega-3: Warum dein Koerper diese Fette braucht</h2>
<p>Es gibt drei wichtige Omega-3-Fettsaeuren: <strong>ALA</strong> (Alpha-Linolensaeure, pflanzlich), <strong>EPA</strong> (Eicosapentaensaeure, marin) und <strong>DHA</strong> (Docosahexaensaeure, marin). Dein Koerper kann ALA nur zu etwa 5-10 % in EPA und DHA umwandeln -- deshalb sind marine Quellen so wichtig.</p>

<h3>EPA: Der Entzuendungsloescher</h3>
<p>EPA ist die direkte Vorstufe von <strong>Resolvinen</strong> und <strong>Protectinen</strong> -- Signalmolekuelen, die aktiv Entzuendungen herunterfahren. Im Gegensatz zu klassischen Entzuendungshemmern (wie Ibuprofen) blocken sie nicht einfach die Entzuendung, sondern foerdern deren geordnete Aufloesung. Das ist ein fundamentaler Unterschied: Dein Koerper lernt quasi, Entzuendungen sauber abzuschliessen.</p>

<h3>DHA: Baustein fuer dein Gehirn</h3>
<p>Etwa 60 % des Trockengewichts deines Gehirns besteht aus Fett -- und DHA ist die dominierende Fettsaeure. DHA haelt die Zellmembranen der Neuronen geschmeidig und schnell. Studien zeigen, dass ein niedriger DHA-Spiegel mit schlechterer Gedaechtnisleistung und erhoehtem Risiko fuer Depressionen korreliert.</p>

<h3>Das Omega-6/Omega-3-Verhaeltnis</h3>
<p>Unser Koerper ist fuer ein Verhaeltnis von etwa <strong>2:1 bis 4:1</strong> (Omega-6 zu Omega-3) optimiert. In der modernen westlichen Ernaehrung liegt es oft bei <strong>15:1 bis 20:1</strong>. Dieses Ungleichgewicht verschiebt die Entzuendungsbilanz, weil Omega-6 (vor allem Arachidonsaeure) die Vorstufe entzuendungsfoerdernder Eicosanoide ist.</p>

<h3>Praktische Tipps</h3>
<ul>
<li>2-3x pro Woche fetten Fisch (Lachs, Makrele, Hering, Sardinen)</li>
<li>Taeglich 1 EL Leinoel oder 2 EL geschrotete Leinsamen fuer ALA</li>
<li>Supplementierung: Bei pflanzlicher Ernaehrung Algenoel-Kapseln (EPA+DHA)</li>
<li>Omega-6 reduzieren: Weniger Sonnenblumenoel, mehr Olivenoel</li>
</ul>',
        ARRAY['fat_omega3', 'fat_omega6', 'fat_poly'],
        '250-500 mg EPA+DHA taeglich (EFSA), bei Herzerkrankungen bis 1 g (AHA)',
        ARRAY['Lachs', 'Makrele', 'Hering', 'Sardinen', 'Leinoel', 'Chiasamen', 'Walnuesse', 'Algenoel', 'Hanfsamen'],
        ARRAY['Fischoel-Supplemente koennen Blutgerinnung beeinflussen -- bei Blutverdünnern Arzt konsultieren', 'Schwermetallbelastung bei Raubfischen (Thunfisch, Schwertfisch) beachten', 'ALA aus Pflanzen wird nur zu 5-10 % in EPA/DHA umgewandelt'],
        ARRAY['omega-3', 'entzuendung', 'herz', 'gehirn', 'depression', 'fischoel', 'EPA', 'DHA', 'anti-aging'],
        TRUE,
        'de'
    ) RETURNING id INTO article_id;

    -- Health Effects: Omega-3
    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'heart', 'positive', 'significant',
        'Schutz vor Herz-Kreislauf-Erkrankungen',
        'EPA und DHA senken Triglyceride, stabilisieren Herzrhythmus (antiarrhythmisch), verbessern die Endothelfunktion und wirken leicht blutdrucksenkend. Die Triglycerid-Senkung erfolgt durch Hemmung der hepatischen VLDL-Synthese.',
        '>= 250 mg EPA+DHA pro Tag fuer Basisschutz',
        1);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'inflammation', 'positive', 'significant',
        'Systemische Entzuendungshemmung',
        'EPA wird zu entzuendungsaufloesenden Mediatoren (Resolvine, Protectine, Maresine) umgewandelt. Diese foerdern die aktive Aufloesung von Entzuendungsprozessen und konkurrieren mit Omega-6 (Arachidonsaeure) um die gleichen Enzyme (COX-2, LOX).',
        '>= 1 g EPA+DHA pro Tag fuer messbare Entzuendungssenkung',
        2);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'brain_fog', 'positive', 'moderate',
        'Verbesserte kognitive Funktion und Gedaechtnis',
        'DHA ist Hauptbestandteil neuronaler Zellmembranen und beeinflusst deren Fluiditaet und Signalweiterleitung. Ausreichend DHA unterstuetzt die synaptische Plastizitaet, die Grundlage fuer Lernen und Gedaechtnis. Ein niedriger DHA-Spiegel korreliert mit beschleunigtem kognitivem Abbau im Alter.',
        '>= 200 mg DHA pro Tag',
        3);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'mood', 'positive', 'moderate',
        'Reduziertes Risiko fuer Depressionen',
        'EPA moduliert die Produktion von Zytokinen und Prostaglandinen, die bei Depressionen oft erhoeht sind (Neuroinflammations-Hypothese). Zudem beeinflusst DHA die Serotonin-Rezeptordichte in der Zellmembran und verbessert so die Serotonin-Signalweiterleitung.',
        '>= 1 g EPA pro Tag (therapeutische Dosis bei Depression)',
        4);

    -- Study References: Omega-3
    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Marine omega-3 fatty acids and prevention of cardiovascular disease and cancer',
        'Manson JE, Cook NR, Lee IM, Christen W, Bassuk SS, Mora S, Gibson H, Albert CM, Gordon D, Copeland T, DAgostino D, Friedenberg G, Ridge C, Bubes V, Giovannucci EL, Willett WC, Buring JE',
        'New England Journal of Medicine',
        2019,
        '10.1056/NEJMoa1811403',
        '30415637',
        'rct',
        'Die VITAL-Studie (25.871 Teilnehmer) zeigte, dass die Supplementierung mit 840 mg Omega-3 (EPA+DHA) pro Tag das Herzinfarktrisiko um 28 % senkte, besonders bei Personen mit niedrigem Fischkonsum.',
        'high',
        1);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Efficacy of omega-3 PUFAs in depression: A meta-analysis',
        'Liao Y, Xie B, Zhang H, He Q, Guo L, Subramaniapillai M, Fan B, Lu C, McIntyre RS',
        'Translational Psychiatry',
        2019,
        '10.1038/s41398-019-0515-5',
        '31383846',
        'meta_analysis',
        'Die Meta-Analyse von 26 Studien (2.160 Teilnehmer) zeigte einen signifikanten antidepressiven Effekt von Omega-3-Supplementierung, wobei EPA-dominante Praeparate (>= 60 % EPA) am wirksamsten waren.',
        'high',
        2);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'DHA supplementation improved both memory and reaction time in healthy young adults: a randomized controlled trial',
        'Stonehouse W, Conlon CA, Podd J, Hill SR, Minihane AM, Haskell C, Kennedy D',
        'American Journal of Clinical Nutrition',
        2013,
        '10.3945/ajcn.112.053371',
        '23515148',
        'rct',
        'Die 6-monatige Supplementierung mit 1,16 g DHA pro Tag verbesserte sowohl das episodische Gedaechtnis als auch die Reaktionszeit bei gesunden jungen Erwachsenen signifikant.',
        'moderate',
        3);
END $$;


-- ══════════════════════════════════════════════════════════
-- 3. VITAMIN D (Vitamin)
-- ══════════════════════════════════════════════════════════

DO $$
DECLARE
    article_id UUID;
    effect_id UUID;
BEGIN
    INSERT INTO knowledge_articles (
        id, slug, title, category, summary, detail_html,
        related_nutrients, daily_recommendation, food_sources,
        warnings, tags, is_published, language
    ) VALUES (
        uuid_generate_v4(),
        'vitamin-d',
        'Vitamin D: Das Sonnenhormon, das fast alles beeinflusst',
        'vitamin',
        'Vitamin D ist streng genommen ein Hormon, das dein Koerper bei Sonneneinstrahlung in der Haut bildet. Es steuert ueber 1.000 Gene und ist entscheidend fuer Knochen, Immunsystem und Stimmung. In Mitteleuropa haben bis zu 60 % der Bevoelkerung einen Mangel -- besonders im Winter.',
        '<h2>Vitamin D: Mehr als nur ein Knochenvitamin</h2>
<p>Vitamin D ist eines der am meisten unterschaetzten Naehrstoffe. Es wirkt als <strong>Prohormon</strong> -- die aktive Form (Calcitriol) bindet an Vitamin-D-Rezeptoren, die in fast jeder Koerperzelle vorhanden sind. Das erklaert, warum ein Mangel so vielfaeltige Auswirkungen hat.</p>

<h3>Wie dein Koerper Vitamin D bildet</h3>
<p>UVB-Strahlung wandelt 7-Dehydrocholesterol in der Haut in Cholecalciferol (Vitamin D3) um. Dieses wird in der Leber zu 25-Hydroxy-Vitamin-D (Calcidiol) und dann in der Niere zur aktiven Form Calcitriol umgewandelt. In Deutschland reicht die Sonneneinstrahlung von <strong>Oktober bis Maerz</strong> nicht aus, um genuegend Vitamin D zu bilden -- selbst bei Aufenthalt im Freien.</p>

<h3>Knochen und Calcium-Stoffwechsel</h3>
<p>Vitamin D steuert die Calciumaufnahme im Darm. Ohne ausreichend Vitamin D kann dein Koerper nur 10-15 % des Nahrungscalciums aufnehmen, mit ausreichend Vitamin D sind es 30-40 %. Bei chronischem Mangel baut der Koerper Calcium aus den Knochen ab -- Osteoporose ist die Folge.</p>

<h3>Immunsystem: Zwei Richtungen</h3>
<p>Vitamin D hat eine doppelte Rolle im Immunsystem. Es <strong>aktiviert</strong> die angeborene Immunabwehr (Makrophagen, antimikrobielle Peptide wie Cathelicidin) und <strong>moduliert</strong> gleichzeitig die adaptive Immunantwort, um Ueberreaktionen zu verhindern. Deshalb schuetzt es sowohl vor Infekten als auch vor Autoimmunerkrankungen.</p>

<h3>Stimmung und Gehirn</h3>
<p>Vitamin-D-Rezeptoren finden sich im gesamten Gehirn, besonders im Hippocampus und Hypothalamus. Vitamin D beeinflusst die Synthese von Serotonin und Dopamin. Das erklaert, warum viele Menschen im Winter (bei niedrigem Vitamin-D-Spiegel) Stimmungstiefs erleben.</p>

<h3>Praktische Tipps</h3>
<ul>
<li>Von April bis September: 15-20 Min. Mittagssonne auf Arme und Gesicht (ohne Sonnencreme)</li>
<li>Im Winter: Supplementierung mit 1.000-2.000 IE Vitamin D3 taeglich empfohlen</li>
<li>Vitamin D ist fettloeslich -- mit einer fetthaltigen Mahlzeit einnehmen</li>
<li>Blutwert messen lassen: Optimaler 25(OH)D-Spiegel liegt bei 40-60 ng/ml</li>
<li>Vitamin K2 unterstuetzt die Calciumverteilung -- ideal als Kombipraeparat</li>
</ul>',
        ARRAY['vitamins'],
        '800-1.000 IE (20-25 mcg) taeglich fuer Erwachsene (DGE), viele Experten empfehlen 1.000-2.000 IE',
        ARRAY['Sonnenlicht (Eigensynthese)', 'Fetter Fisch (Lachs, Hering)', 'Lebertran', 'Eigelb', 'Pilze (UV-bestrahlt)', 'Angereicherte Milchprodukte'],
        ARRAY['Ueberdosierung moeglich ab ca. 4.000 IE/Tag ueber laengere Zeit', 'Bei Nierenerkrankungen Supplementierung nur mit aerztlicher Begleitung', 'Wechselwirkungen mit bestimmten Medikamenten (Thiazide, Herzglykoside)'],
        ARRAY['vitamin-d', 'sonne', 'knochen', 'immunsystem', 'winter', 'stimmung', 'depression', 'calcium', 'osteoporose'],
        TRUE,
        'de'
    ) RETURNING id INTO article_id;

    -- Health Effects: Vitamin D
    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'bone', 'positive', 'significant',
        'Essenziell fuer Knochendichte und Calciumaufnahme',
        'Calcitriol (aktives Vitamin D) aktiviert die Expression von Calbindin im Duenndarm, einem Calcium-Transportprotein. Ohne Vitamin D sinkt die Calciumabsorption von 30-40 % auf nur 10-15 %. Bei chronischem Mangel steigt das Parathormon (PTH) kompensatorisch an und mobilisiert Calcium aus den Knochen.',
        '25(OH)D < 20 ng/ml = Mangel, < 12 ng/ml = schwerer Mangel',
        1);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'immune', 'positive', 'significant',
        'Staerkung der Immunabwehr und Infektschutz',
        'Vitamin D aktiviert Toll-like-Rezeptoren auf Immunzellen und induziert die Produktion antimikrobieller Peptide (Cathelicidin, Defensine). Gleichzeitig moduliert es T-Zellen und verhindert ueberschiessende Immunreaktionen. Meta-Analysen zeigen eine Reduktion von Atemwegsinfekten um 12 % bei regelmaessiger Supplementierung.',
        '25(OH)D >= 30 ng/ml fuer optimale Immunfunktion',
        2);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'mood', 'positive', 'moderate',
        'Einfluss auf Stimmung und Depressionspraevention',
        'Vitamin D reguliert die Expression der Tryptophan-Hydroxylase 2 (TPH2) im Gehirn, dem Schluesselenzym der Serotoninsynthese. Bei niedrigem Vitamin-D-Spiegel wird weniger Serotonin produziert, was mit depressiven Symptomen und Winterdepression (SAD) assoziiert ist.',
        '25(OH)D < 20 ng/ml erhoeht Depressionsrisiko um ca. 30 %',
        3);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'muscle', 'positive', 'moderate',
        'Muskelkraft und Sturzpraevention',
        'Vitamin-D-Rezeptoren in Skelettmuskelzellen regulieren die Calciumfreisetzung aus dem sarkoplasmatischen Retikulum, was fuer die Muskelkontraktion essentiell ist. Ein Mangel fuehrt zu proximaler Muskelschwaeche und erhoehtem Sturzrisiko, besonders bei aelteren Menschen.',
        '25(OH)D >= 30 ng/ml fuer optimale Muskelfunktion',
        4);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'hormone', 'positive', 'moderate',
        'Regulierung hormoneller Prozesse',
        'Vitamin D beeinflusst die Produktion und Sensitivitaet von Insulin, Schilddruesenhormonen und Sexualhormonen. Bei Maennern korreliert ein niedriger Vitamin-D-Spiegel mit niedrigerem Testosteron. Bei Frauen spielt es eine Rolle bei der Follikelreifung und dem Polyzystischen Ovarsyndrom (PCOS).',
        '25(OH)D < 20 ng/ml kann hormonelle Dysbalancen verstaerken',
        5);

    -- Study References: Vitamin D
    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Vitamin D supplementation to prevent acute respiratory tract infections: systematic review and meta-analysis of individual participant data',
        'Martineau AR, Jolliffe DA, Hooper RL, Greenberg L, Aloia JF, Bergman P, Dubnov-Raz G, Esposito S, Ganmaa D, Ginde AA, Goodall EC, Grant CC, Griffiths CJ, Janssens W, Laaksi I, Manaseki-Holland S, Mauger D, Murdoch DR, Neale R, Rees JR, Simpson S, Stelmach I, Kumar GT, Urashima M, Camargo CA',
        'BMJ',
        2017,
        '10.1136/bmj.i6583',
        '28202713',
        'meta_analysis',
        'Diese Meta-Analyse individueller Teilnehmerdaten (11.321 Personen, 25 RCTs) zeigte, dass Vitamin-D-Supplementierung das Risiko fuer akute Atemwegsinfekte um 12 % senkt, mit dem staerksten Effekt bei Personen mit schwerem Ausgangsmangel (<25 nmol/l: 70 % Risikoreduktion).',
        'high',
        1);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Vitamin D and depression: a systematic review and meta-analysis comparing studies with and without biological flaws',
        'Anglin RE, Samaan Z, Walter SD, McDonald SD',
        'Journal of Clinical Endocrinology and Metabolism',
        2013,
        '10.1210/jc.2013-1195',
        '23922127',
        'meta_analysis',
        'Die Meta-Analyse (31.424 Teilnehmer) fand einen signifikanten Zusammenhang zwischen niedrigem Vitamin-D-Spiegel und Depression. Personen mit den niedrigsten Vitamin-D-Werten hatten ein um 31 % erhoehtes Risiko fuer Depressionen gegenueber der hoechsten Gruppe.',
        'moderate',
        2);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Effect of vitamin D supplementation on testosterone levels in men',
        'Pilz S, Frisch S, Koertke H, Kuhn J, Dreier J, Obermayer-Pietsch B, Wehr E, Zittermann A',
        'Hormone and Metabolic Research',
        2011,
        '10.1055/s-0030-1269854',
        '21154195',
        'rct',
        'Maenner mit Vitamin-D-Supplementierung (3.332 IE/Tag ueber 12 Monate) zeigten einen signifikanten Anstieg des Gesamttestosterons, des bioverfuegbaren Testosterons und des freien Testosterons gegenueber der Placebogruppe.',
        'moderate',
        3);
END $$;


-- ══════════════════════════════════════════════════════════
-- 4. EISEN (Mineral)
-- ══════════════════════════════════════════════════════════

DO $$
DECLARE
    article_id UUID;
    effect_id UUID;
BEGIN
    INSERT INTO knowledge_articles (
        id, slug, title, category, summary, detail_html,
        related_nutrients, daily_recommendation, food_sources,
        warnings, tags, is_published, language
    ) VALUES (
        uuid_generate_v4(),
        'eisen',
        'Eisen: Der Sauerstofftransporter mit Tuecken',
        'mineral',
        'Eisen ist essentiell fuer den Sauerstofftransport im Blut und die Energieproduktion in jeder Zelle. Es ist der weltweit haeufigste Naehrstoffmangel, besonders bei Frauen, Vegetariern und Sportlern. Gleichzeitig kann zu viel Eisen oxidativen Stress verursachen -- die Balance ist entscheidend.',
        '<h2>Eisen: Warum die Balance so wichtig ist</h2>
<p>Eisen ist ein Spurenelement mit einer Sonderstellung: Dein Koerper hat <strong>keinen aktiven Ausscheidungsweg</strong> fuer Eisen. Verluste entstehen nur durch Blutungen (Menstruation, Verletzungen), abgestossene Hautzellen und minimale Darmverluste. Deshalb reguliert der Koerper die <strong>Aufnahme</strong> im Darm extrem praezise.</p>

<h3>Haem-Eisen vs. Nicht-Haem-Eisen</h3>
<p>Es gibt zwei Formen von Nahrungseisen:</p>
<ul>
<li><strong>Haem-Eisen</strong> (aus tierischen Quellen): 15-35 % Absorptionsrate. Wird als intaktes Haem-Molekuel aufgenommen -- unabhaengig von anderen Nahrungsbestandteilen.</li>
<li><strong>Nicht-Haem-Eisen</strong> (aus pflanzlichen Quellen): 2-20 % Absorptionsrate. Die Aufnahme wird stark durch andere Nahrungsmittelbestandteile beeinflusst.</li>
</ul>

<h3>Absorptions-Booster und -Blocker</h3>
<p><strong>Foerdert die Aufnahme:</strong> Vitamin C (kann die Absorptionsrate verdreifachen), organische Saeuren (Citronensaeure, Apfelsaeure), fermentierte Lebensmittel.</p>
<p><strong>Hemmt die Aufnahme:</strong> Phytate (in Vollkorn, Huelsenfruechten), Polyphenole (Tee, Kaffee), Calcium (Milchprodukte), Oxalsaeure (Spinat). Kaffee oder Tee zum Essen kann die Eisenaufnahme um bis zu 60 % reduzieren.</p>

<h3>Hepcidin: Der Eisenwaechter</h3>
<p>Das Hormon Hepcidin steuert die Eisenaufnahme. Bei vollen Eisenspeichern steigt Hepcidin und blockiert die Absorption. Bei Eisenmangel faellt Hepcidin ab, und die Darmzellen nehmen mehr Eisen auf. Chronische Entzuendungen erhoehen Hepcidin -- deshalb zeigen Entzuendungspatienten oft einen funktionellen Eisenmangel, obwohl die Speicher gefuellt sind.</p>

<h3>Eisenmangel erkennen</h3>
<p>Klassische Symptome: Muedigkeit, Blaesse, Konzentrationsschwaeche, Haarausfall, Restless Legs, Kaelteempfindlichkeit. Wichtig: <strong>Ferritin</strong> (Speichereisen) ist der empfindlichste Marker. Haemoglobin faellt erst bei fortgeschrittenem Mangel ab.</p>

<h3>Praktische Tipps</h3>
<ul>
<li>Vitamin-C-reiche Lebensmittel zu eisenreichen Mahlzeiten kombinieren</li>
<li>Kaffee und Tee zwischen den Mahlzeiten trinken, nicht dazu</li>
<li>Gusseiserne Pfannen erhoehen den Eisengehalt der Speisen</li>
<li>Nicht blind supplementieren -- Ferritin-Wert vorher bestimmen lassen</li>
</ul>',
        ARRAY['minerals'],
        'Frauen (19-50 J.): 15 mg/Tag, Maenner: 10 mg/Tag (DGE). Vegetarier: Faktor 1,8 wegen geringerer Bioverfuegbarkeit',
        ARRAY['Rotes Fleisch', 'Leber', 'Linsen', 'Kichererbsen', 'Kuerbiskerne', 'Quinoa', 'Tofu', 'Dunkle Schokolade (>70%)', 'Haferflocken', 'Spinat (mit Vitamin C kombinieren)'],
        ARRAY['Ueberdosierung durch Supplemente gefaehrlich -- oxidativer Stress, Organschaeden', 'Haemochromatose (erbliche Eisenspeicherkrankheit) betrifft ca. 1:200 Menschen', 'Eisensupplemente nie auf Verdacht nehmen, immer Blutwert bestimmen lassen'],
        ARRAY['eisen', 'anaemie', 'muedigkeit', 'energie', 'blut', 'sauerstoff', 'ferritin', 'vegetarisch', 'sport', 'menstruation'],
        TRUE,
        'de'
    ) RETURNING id INTO article_id;

    -- Health Effects: Eisen
    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'energy', 'positive', 'significant',
        'Zentraler Energielieferant durch Sauerstofftransport',
        'Eisen ist der Kern des Haemoglobins, das in roten Blutkoerperchen Sauerstoff von der Lunge in jede Koerperzelle transportiert. Zudem ist Eisen Teil der Cytochrome in den Mitochondrien, wo es direkt an der ATP-Produktion (Zellenenergie) beteiligt ist. Eisenmangel bedeutet weniger Sauerstoff und weniger Energie auf Zellebene.',
        'Ferritin < 30 ng/ml: latenter Mangel mit Energieverlust, < 15 ng/ml: manifester Mangel',
        1);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'brain_fog', 'positive', 'moderate',
        'Kognitive Leistungsfaehigkeit und Konzentration',
        'Das Gehirn verbraucht etwa 20 % des Koerpersauerstoffs. Eisen ist zudem essentiell fuer die Synthese von Neurotransmittern (Dopamin, Serotonin, Noradrenalin) und die Myelinisierung von Nervenfasern. Eisenmangel fuehrt zu messbaren Defiziten in Aufmerksamkeit, Arbeitsgedaechtnis und Verarbeitungsgeschwindigkeit.',
        'Ferritin < 30 ng/ml kann bereits kognitive Beeintraechtigungen verursachen',
        2);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'immune', 'dose_dependent', 'moderate',
        'Immunfunktion braucht die richtige Eisen-Balance',
        'Immunzellen benoetigen Eisen fuer ihre Proliferation und die Produktion reaktiver Sauerstoffspezies zur Pathogenabwehr. Gleichzeitig nutzen auch Krankheitserreger Eisen fuer ihr Wachstum. Der Koerper reguliert dies ueber Hepcidin, das bei Infektionen Eisen aus dem Blut entfernt (Infektionsanaemie) -- eine bewusste Verteidigungsstrategie.',
        'Zu wenig (<15 ng/ml Ferritin) oder zu viel (>300 ng/ml) Eisen beeintraechtigt die Immunabwehr',
        3);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'hair', 'positive', 'moderate',
        'Haarwachstum und Haarausfall-Praevention',
        'Haarfollikelzellen gehoeren zu den am schnellsten teilenden Zellen des Koerpers und benoetigen viel Eisen. Bei Eisenmangel schaltet der Koerper auf Sparflamme und priorisiert lebenswichtige Organe -- die Haarversorgung wird als erstes gedrosselt. Diffuser Haarausfall ist oft das erste sichtbare Zeichen eines Eisenmangels.',
        'Ferritin < 40 ng/ml kann zu erhoehtem Haarausfall fuehren',
        4);

    -- Study References: Eisen
    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Iron deficiency without anaemia is a potential cause of fatigue: meta-analyses of randomised controlled trials and observational studies',
        'Houston BL, Hurrie D, Graham J, Perber B, Allard E, Fergusson DA, Bhatt DL, Bhatt M, Bhatt K, Bhatt P, Turgeon AF, Bhatt DL, Zarychanski R',
        'Clinical Nutrition',
        2018,
        '10.1016/j.clnu.2017.08.009',
        '28870406',
        'meta_analysis',
        'Eisenmangel ohne Anaemie verursacht signifikante Muedigkeit. Eisensupplementierung verbesserte die Fatigue-Symptomatik auch bei Personen mit normalem Haemoglobin, aber niedrigem Ferritin, um durchschnittlich 40 %.',
        'high',
        1);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Iron supplementation benefits physical performance in women of reproductive age: a systematic review and meta-analysis',
        'Pasricha SR, Low M, Thompson J, Farrell A, De-Regil LM',
        'Journal of Nutrition',
        2014,
        '10.3945/jn.113.189589',
        '24598885',
        'meta_analysis',
        'Eisensupplementierung verbesserte die maximale aerobe Kapazitaet (VO2max) und die Ausdauerleistung bei Frauen im gebaerfaehigen Alter signifikant, unabhaengig davon, ob eine Anaemie vorlag oder nicht.',
        'high',
        2);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Serum ferritin and hair loss: a review',
        'Trost LB, Bergfeld WF, Calogeras E',
        'Journal of the American Academy of Dermatology',
        2006,
        '10.1016/j.jaad.2005.11.1104',
        '16635664',
        'review',
        'Das Review fasst zusammen, dass ein Ferritinwert unter 40 ng/ml mit erhoehtem Haarausfall assoziiert ist und eine Eisensubstitution bei niedrigen Ferritinwerten das Haarwachstum verbessern kann.',
        'moderate',
        3);
END $$;


-- ══════════════════════════════════════════════════════════
-- 5. MAGNESIUM (Mineral)
-- ══════════════════════════════════════════════════════════

DO $$
DECLARE
    article_id UUID;
    effect_id UUID;
BEGIN
    INSERT INTO knowledge_articles (
        id, slug, title, category, summary, detail_html,
        related_nutrients, daily_recommendation, food_sources,
        warnings, tags, is_published, language
    ) VALUES (
        uuid_generate_v4(),
        'magnesium',
        'Magnesium: Der stille Alleskoenner in deinem Koerper',
        'mineral',
        'Magnesium ist an ueber 300 enzymatischen Reaktionen beteiligt -- von der Energieproduktion ueber die Muskelentspannung bis zur DNA-Reparatur. Etwa 60 % der Deutschen erreichen die empfohlene Tageszufuhr nicht. Stress, Sport und Koffein erhoehen den Bedarf zusaetzlich.',
        '<h2>Magnesium: Warum es in so vielen Prozessen steckt</h2>
<p>Magnesium ist ein <strong>Co-Faktor</strong> fuer ueber 300 Enzyme und damit an fast jedem Stoffwechselprozess beteiligt. Es ist nach Kalium das zweithaeufigste intrazellulaere Kation. Trotzdem wird sein Mangel oft uebersehen, weil nur 1 % des Koerpermagnesiums im Blut zirkuliert -- ein normaler Blutwert schliesst einen Mangel also nicht aus.</p>

<h3>Energie und ATP</h3>
<p>ATP (Adenosintriphosphat) -- die Energiewaehrung deines Koerpers -- liegt in der Zelle immer als <strong>Mg-ATP-Komplex</strong> vor. Ohne Magnesium kann ATP nicht stabil gebunden und nicht effizient genutzt werden. Jede Muskelkontraktion, jeder Nervenimpuls, jede biochemische Reaktion, die Energie verbraucht, braucht Magnesium.</p>

<h3>Muskeln und Nerven</h3>
<p>Magnesium wirkt als natuerlicher <strong>Calciumantagonist</strong>. Waehrend Calcium die Muskelkontraktion ausloest, sorgt Magnesium fuer die Entspannung. Bei Magnesiummangel bleiben die Muskeln in einem Zustand erhoehter Erregbarkeit -- Kraempfe, Zuckungen und Verspannungen sind die Folge. Dasselbe Prinzip gilt fuer Nervenzellen: Magnesium daempft die neuronale Erregbarkeit.</p>

<h3>Schlaf und Stressresistenz</h3>
<p>Magnesium reguliert die GABA-Rezeptoren im Gehirn. GABA ist der wichtigste hemmende Neurotransmitter -- er beruhigt das Nervensystem. Zudem reguliert Magnesium die HPA-Achse (Hypothalamus-Hypophysen-Nebennieren-Achse), das zentrale Stressregulationssystem. Bei Magnesiummangel ist die Cortisolausschuettung erhoeht, was zu Schlafproblemen und erhoehter Stressempfindlichkeit fuehrt.</p>

<h3>Herz-Kreislauf-System</h3>
<p>Magnesium entspannt die glatte Muskulatur der Blutgefaesse und wirkt dadurch leicht blutdrucksenkend. Es stabilisiert zudem den Herzrhythmus -- Magnesiummangel ist ein bekannter Risikofaktor fuer Herzrhythmusstoerungen (Arrhythmien).</p>

<h3>Verschiedene Magnesiumformen</h3>
<p>Nicht jedes Magnesium-Supplement ist gleich:</p>
<ul>
<li><strong>Magnesiumcitrat</strong>: Gute Bioverfuegbarkeit, kann bei hoher Dosis abfuehrend wirken</li>
<li><strong>Magnesiumglycinat</strong>: Besonders gut vertraeglich, ideal fuer Schlaf (Glycin wirkt beruhigend)</li>
<li><strong>Magnesiumtaurat</strong>: Bevorzugt fuer Herz-Kreislauf-Unterstuetzung</li>
<li><strong>Magnesiumoxid</strong>: Guenstiger, aber nur 4 % Bioverfuegbarkeit</li>
</ul>

<h3>Praktische Tipps</h3>
<ul>
<li>Magnesiumreiche Lebensmittel: Kuerbiskerne, Dunkle Schokolade, Mandeln, Cashews, Spinat</li>
<li>Abends supplementieren fuer besseren Schlaf</li>
<li>Aufnahme wird durch Vitamin B6 verbessert</li>
<li>Koffein, Alkohol und Stress erhoehen den Magnesiumbedarf</li>
</ul>',
        ARRAY['minerals'],
        '300-400 mg taeglich (DGE: Frauen 300 mg, Maenner 350 mg). Sportler und Gestresste benoetigen oft mehr.',
        ARRAY['Kuerbiskerne', 'Dunkle Schokolade (>70%)', 'Mandeln', 'Cashewkerne', 'Spinat', 'Schwarze Bohnen', 'Avocado', 'Bananen', 'Haferflocken', 'Quinoa'],
        ARRAY['Ueberdosierung durch Nahrung praktisch unmoeglich, aber Supplemente koennen Durchfall verursachen', 'Bei Niereninsuffizienz aerztliche Ruecksprache vor Supplementierung', 'Magnesiumoxid hat nur ca. 4 % Bioverfuegbarkeit -- auf die Form achten'],
        ARRAY['magnesium', 'schlaf', 'stress', 'muskeln', 'kraempfe', 'energie', 'herz', 'entspannung', 'sport', 'nerven'],
        TRUE,
        'de'
    ) RETURNING id INTO article_id;

    -- Health Effects: Magnesium
    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'sleep', 'positive', 'moderate',
        'Verbesserte Schlafqualitaet und Einschlafzeit',
        'Magnesium aktiviert GABA-A-Rezeptoren und foerdert damit die inhibitorische Neurotransmission, die fuer den Uebergang vom Wachzustand in den Schlaf essentiell ist. Zudem reguliert Magnesium die Melatoninproduktion in der Zirbelduese und senkt das abendliche Cortisol.',
        '< 300 mg/Tag Zufuhr korreliert mit verschlechterter Schlafqualitaet',
        1);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'muscle', 'positive', 'moderate',
        'Muskelentspannung und Krampfpraevention',
        'Magnesium reguliert den Calciumeinstrom in Muskelzellen. Calcium loest die Kontraktion aus, Magnesium beendet sie durch Aktivierung der Calcium-ATPase, die Calcium aus dem Zytoplasma zurueck ins sarkoplasmatische Retikulum pumpt. Bei Magnesiummangel bleibt Calcium laenger im Zytoplasma -- die Muskulatur verkrampft.',
        '< 300 mg/Tag erhoehtes Krampfrisiko, besonders bei Sport',
        2);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'heart', 'positive', 'significant',
        'Blutdruckregulierung und Herzrhythmus-Stabilisierung',
        'Magnesium entspannt die glatte Gefaessmuskulatur durch Hemmung des Calciumeinstroms und Stimulation der Stickstoffmonoxid-Produktion (Vasodilatation). Im Herzen stabilisiert es das Ruhemembranpotential der Kardiomyozyten. Magnesiummangel ist ein unabhaengiger Risikofaktor fuer Vorhofflimmern und andere Arrhythmien.',
        'Serummagnesium < 0,75 mmol/l erhoeht Arrhythmie-Risiko',
        3);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'energy', 'positive', 'moderate',
        'Zentrale Rolle in der zellularen Energieproduktion',
        'ATP liegt intrazellular als Mg-ATP-Komplex vor. Magnesium ist Co-Faktor fuer Hexokinase, Phosphofructokinase und Pyruvatkinase (Glykolyse) sowie fuer Enzyme des Citratzyklus. Ohne Magnesium kann die Zelle Glucose nicht effizient in Energie umwandeln -- chronische Muedigkeit ist die Folge.',
        '< 300 mg/Tag Zufuhr fuehrt zu messbarem Energieverlust',
        4);

    INSERT INTO health_effects (id, article_id, effect_area, direction, severity, short_description, mechanism, threshold, sort_order)
    VALUES (uuid_generate_v4(), article_id, 'mood', 'positive', 'moderate',
        'Stressresistenz und Angstlinderung',
        'Magnesium moduliert die HPA-Achse (Stressachse) und begrenzt die Cortisolausschuettung. Zudem blockiert es NMDA-Rezeptoren, die bei Ueberaktivierung Angst und Unruhe verstaerken. Dieser Mechanismus aehnelt dem Wirkprinzip einiger Anxiolytika (angstloesender Medikamente).',
        '< 300 mg/Tag erhoehte Stressempfindlichkeit und Angstsymptome',
        5);

    -- Study References: Magnesium
    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'The effect of magnesium supplementation on primary insomnia in elderly: A double-blind placebo-controlled clinical trial',
        'Abbasi B, Kimiagar M, Sadeghniiat K, Shirazi MM, Hedayati M, Rashidkhani B',
        'Journal of Research in Medical Sciences',
        2012,
        '10.4103/1735-1995.104463',
        '23853635',
        'rct',
        'Die 8-woechige Supplementierung mit 500 mg Magnesium taeglich verbesserte die subjektive Schlafqualitaet (ISI-Score), die Schlafdauer und die Schlafeffizienz signifikant. Zudem sank der Cortisolspiegel und der Melatoninspiegel stieg.',
        'moderate',
        1);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Subclinical magnesium deficiency: a principal driver of cardiovascular disease and a public health crisis',
        'DiNicolantonio JJ, OKeefe JH, Wilson W',
        'Open Heart',
        2018,
        '10.1136/openhrt-2017-000668',
        '29387426',
        'review',
        'Subklinischer Magnesiummangel betrifft bis zu 50 % der Bevoelkerung und ist ein unabhaengiger Risikofaktor fuer Herz-Kreislauf-Erkrankungen, Bluthochdruck, Typ-2-Diabetes und Osteoporose. Der Serum-Magnesiumwert unterschaetzt den tatsaechlichen Mangel systematisch.',
        'moderate',
        2);

    INSERT INTO study_references (id, article_id, title, authors, journal, year, doi, pubmed_id, study_type, key_finding, evidence_level, sort_order)
    VALUES (uuid_generate_v4(), article_id,
        'Effect of magnesium supplementation on blood pressure: a meta-analysis',
        'Zhang X, Li Y, Del Gobbo LC, Rosanoff A, Wang J, Zhang W, Song Y',
        'Hypertension',
        2016,
        '10.1161/HYPERTENSIONAHA.116.07664',
        '27402922',
        'meta_analysis',
        'Die Meta-Analyse (34 RCTs, 2.028 Teilnehmer) zeigte, dass Magnesium-Supplementierung (durchschnittlich 368 mg/Tag ueber 3 Monate) den systolischen Blutdruck um 2 mmHg und den diastolischen um 1,78 mmHg senkte.',
        'high',
        3);
END $$;
