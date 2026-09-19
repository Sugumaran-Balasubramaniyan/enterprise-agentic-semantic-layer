"""Deterministic generator for high-fidelity SAP Enterprise Support Knowledge Graph.

Synthesizes interconnected multi-source RDF data:
- PPMS product and software lifecycle hierarchy
- Application component taxonomies
- System alerts and ABAP runtime dumps
- SimCat problem categories
- SAP Notes with symptoms, resolutions, and prerequisite dependency chains
- Official Help Documentation references
"""

from __future__ import annotations

from pathlib import Path

from rdflib import RDF, RDFS, XSD, Graph, Literal, Namespace, URIRef

PPMS = Namespace("http://ontology.sap.com/ppms#")
SAP = Namespace("http://ontology.sap.com/support#")


def build_sap_support_graph(ontology_paths: list[str | Path] | None = None) -> Graph:
    """Build and populate the SAP Enterprise Support Knowledge Graph."""
    g = Graph()
    g.bind("ppms", PPMS)
    g.bind("sap", SAP)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)

    # Load base ontologies if provided
    if ontology_paths:
        for p in ontology_paths:
            g.parse(location=str(p), format="turtle")

    # -------------------------------------------------------------
    # 1. PPMS Product Line & Products
    # -------------------------------------------------------------
    pl_s4 = URIRef("http://data.sap.com/ppms/productline/S4HANA")
    g.add((pl_s4, RDF.type, PPMS.ProductLine))
    g.add((pl_s4, RDFS.label, Literal("SAP S/4HANA Product Line", lang="en")))
    g.add((pl_s4, PPMS.productLineCode, Literal("S4HANA", datatype=XSD.string)))

    pl_nw = URIRef("http://data.sap.com/ppms/productline/NETWEAVER")
    g.add((pl_nw, RDF.type, PPMS.ProductLine))
    g.add((pl_nw, RDFS.label, Literal("SAP NetWeaver Platform", lang="en")))
    g.add((pl_nw, PPMS.productLineCode, Literal("NETWEAVER", datatype=XSD.string)))

    prod_s4_onprem = URIRef("http://data.sap.com/ppms/product/S4HANA_ONPREM")
    g.add((prod_s4_onprem, RDF.type, PPMS.Product))
    g.add((prod_s4_onprem, RDFS.label, Literal("SAP S/4HANA On-Premise", lang="en")))
    g.add((prod_s4_onprem, PPMS.belongsToProductLine, pl_s4))
    g.add((prod_s4_onprem, PPMS.productCode, Literal("S4HANA_ONPREM", datatype=XSD.string)))

    prod_nw_abap = URIRef("http://data.sap.com/ppms/product/NW_ABAP")
    g.add((prod_nw_abap, RDF.type, PPMS.Product))
    g.add((prod_nw_abap, RDFS.label, Literal("SAP NetWeaver Application Server ABAP", lang="en")))
    g.add((prod_nw_abap, PPMS.belongsToProductLine, pl_nw))

    # -------------------------------------------------------------
    # 2. PPMS Software Components
    # -------------------------------------------------------------
    sc_basis = URIRef("http://data.sap.com/ppms/component/SAP_BASIS")
    g.add((sc_basis, RDF.type, PPMS.SoftwareComponent))
    g.add((sc_basis, RDFS.label, Literal("SAP Basis Component (System Infrastructure)", lang="en")))
    g.add((sc_basis, PPMS.componentName, Literal("SAP_BASIS", datatype=XSD.string)))

    sc_s4core = URIRef("http://data.sap.com/ppms/component/S4CORE")
    g.add((sc_s4core, RDF.type, PPMS.SoftwareComponent))
    g.add((sc_s4core, RDFS.label, Literal("S/4HANA Core Application Logic", lang="en")))
    g.add((sc_s4core, PPMS.componentName, Literal("S4CORE", datatype=XSD.string)))

    sc_appl = URIRef("http://data.sap.com/ppms/component/SAP_APPL")
    g.add((sc_appl, RDF.type, PPMS.SoftwareComponent))
    g.add((sc_appl, RDFS.label, Literal("SAP Logistics and Accounting Core", lang="en")))
    g.add((sc_appl, PPMS.componentName, Literal("SAP_APPL", datatype=XSD.string)))

    # -------------------------------------------------------------
    # 3. PPMS Product Versions & Component Versions
    # -------------------------------------------------------------
    # S/4HANA 2023
    pv_s4_2023 = URIRef("http://data.sap.com/ppms/version/S4HANA_2023")
    g.add((pv_s4_2023, RDF.type, PPMS.ProductVersion))
    g.add((pv_s4_2023, RDFS.label, Literal("SAP S/4HANA 2023 Release", lang="en")))
    g.add((pv_s4_2023, PPMS.versionCode, Literal("S4HANA_2023", datatype=XSD.string)))
    g.add((pv_s4_2023, PPMS.releaseYear, Literal(2023, datatype=XSD.integer)))
    g.add((prod_s4_onprem, PPMS.hasProductVersion, pv_s4_2023))

    scv_basis_758 = URIRef("http://data.sap.com/ppms/compversion/SAP_BASIS_758")
    g.add((scv_basis_758, RDF.type, PPMS.SoftwareComponentVersion))
    g.add((scv_basis_758, RDFS.label, Literal("SAP_BASIS 758", lang="en")))
    g.add((scv_basis_758, PPMS.componentVersionString, Literal("758", datatype=XSD.string)))
    g.add((scv_basis_758, PPMS.isVersionOfComponent, sc_basis))
    g.add((pv_s4_2023, PPMS.includesComponent, scv_basis_758))

    scv_s4core_108 = URIRef("http://data.sap.com/ppms/compversion/S4CORE_108")
    g.add((scv_s4core_108, RDF.type, PPMS.SoftwareComponentVersion))
    g.add((scv_s4core_108, RDFS.label, Literal("S4CORE 108", lang="en")))
    g.add((scv_s4core_108, PPMS.componentVersionString, Literal("108", datatype=XSD.string)))
    g.add((scv_s4core_108, PPMS.isVersionOfComponent, sc_s4core))
    g.add((pv_s4_2023, PPMS.includesComponent, scv_s4core_108))

    # S/4HANA 2022
    pv_s4_2022 = URIRef("http://data.sap.com/ppms/version/S4HANA_2022")
    g.add((pv_s4_2022, RDF.type, PPMS.ProductVersion))
    g.add((pv_s4_2022, RDFS.label, Literal("SAP S/4HANA 2022 Release", lang="en")))
    g.add((pv_s4_2022, PPMS.versionCode, Literal("S4HANA_2022", datatype=XSD.string)))
    g.add((pv_s4_2022, PPMS.releaseYear, Literal(2022, datatype=XSD.integer)))
    g.add((prod_s4_onprem, PPMS.hasProductVersion, pv_s4_2022))

    scv_basis_757 = URIRef("http://data.sap.com/ppms/compversion/SAP_BASIS_757")
    g.add((scv_basis_757, RDF.type, PPMS.SoftwareComponentVersion))
    g.add((scv_basis_757, RDFS.label, Literal("SAP_BASIS 757", lang="en")))
    g.add((scv_basis_757, PPMS.componentVersionString, Literal("757", datatype=XSD.string)))
    g.add((scv_basis_757, PPMS.isVersionOfComponent, sc_basis))
    g.add((pv_s4_2022, PPMS.includesComponent, scv_basis_757))

    # Support Packages for SAP_BASIS 758 (SP00, SP01, SP02, SP03)
    for sp_level in range(4):
        sp_uri = URIRef(f"http://data.sap.com/ppms/sp/SAP_BASIS_758_SP{sp_level:02d}")
        g.add((sp_uri, RDF.type, PPMS.SupportPackage))
        g.add((sp_uri, RDFS.label, Literal(f"SAP_BASIS 758 SP{sp_level:02d}", lang="en")))
        g.add((sp_uri, PPMS.stackLevel, Literal(sp_level, datatype=XSD.integer)))
        g.add((sp_uri, PPMS.spName, Literal(f"SP{sp_level:02d}", datatype=XSD.string)))
        g.add((scv_basis_758, PPMS.hasSupportPackage, sp_uri))

    # -------------------------------------------------------------
    # 4. Application Components Hierarchy
    # -------------------------------------------------------------
    # BC (Basis)
    comp_bc = URIRef("http://data.sap.com/support/component/BC")
    g.add((comp_bc, RDF.type, SAP.ApplicationComponent))
    g.add((comp_bc, SAP.componentCode, Literal("BC", datatype=XSD.string)))
    g.add((comp_bc, SAP.componentDescription, Literal("Basis Components", lang="en")))

    comp_bc_db = URIRef("http://data.sap.com/support/component/BC-DB")
    g.add((comp_bc_db, RDF.type, SAP.ApplicationComponent))
    g.add((comp_bc_db, SAP.componentCode, Literal("BC-DB", datatype=XSD.string)))
    g.add((comp_bc_db, SAP.componentDescription, Literal("Database Interface and Infrastructure", lang="en")))
    g.add((comp_bc_db, SAP.parentComponent, comp_bc))

    comp_bc_db_hdb = URIRef("http://data.sap.com/support/component/BC-DB-HDB")
    g.add((comp_bc_db_hdb, RDF.type, SAP.ApplicationComponent))
    g.add((comp_bc_db_hdb, SAP.componentCode, Literal("BC-DB-HDB", datatype=XSD.string)))
    g.add((comp_bc_db_hdb, SAP.componentDescription, Literal("SAP HANA Database Interface", lang="en")))
    g.add((comp_bc_db_hdb, SAP.parentComponent, comp_bc_db))

    comp_bc_cst = URIRef("http://data.sap.com/support/component/BC-CST")
    g.add((comp_bc_cst, RDF.type, SAP.ApplicationComponent))
    g.add((comp_bc_cst, SAP.componentCode, Literal("BC-CST", datatype=XSD.string)))
    g.add((comp_bc_cst, SAP.componentDescription, Literal("Client Server Technology", lang="en")))
    g.add((comp_bc_cst, SAP.parentComponent, comp_bc))

    comp_bc_cst_mm = URIRef("http://data.sap.com/support/component/BC-CST-MM")
    g.add((comp_bc_cst_mm, RDF.type, SAP.ApplicationComponent))
    g.add((comp_bc_cst_mm, SAP.componentCode, Literal("BC-CST-MM", datatype=XSD.string)))
    g.add((comp_bc_cst_mm, SAP.componentDescription, Literal("Memory Management & Work Processes", lang="en")))
    g.add((comp_bc_cst_mm, SAP.parentComponent, comp_bc_cst))

    # FI (Financials)
    comp_fi = URIRef("http://data.sap.com/support/component/FI")
    g.add((comp_fi, RDF.type, SAP.ApplicationComponent))
    g.add((comp_fi, SAP.componentCode, Literal("FI", datatype=XSD.string)))
    g.add((comp_fi, SAP.componentDescription, Literal("Financial Accounting", lang="en")))

    comp_fi_gl = URIRef("http://data.sap.com/support/component/FI-GL")
    g.add((comp_fi_gl, RDF.type, SAP.ApplicationComponent))
    g.add((comp_fi_gl, SAP.componentCode, Literal("FI-GL", datatype=XSD.string)))
    g.add((comp_fi_gl, SAP.componentDescription, Literal("General Ledger Accounting", lang="en")))
    g.add((comp_fi_gl, SAP.parentComponent, comp_fi))

    comp_fi_gl_gl = URIRef("http://data.sap.com/support/component/FI-GL-GL")
    g.add((comp_fi_gl_gl, RDF.type, SAP.ApplicationComponent))
    g.add((comp_fi_gl_gl, SAP.componentCode, Literal("FI-GL-GL", datatype=XSD.string)))
    g.add((comp_fi_gl_gl, SAP.componentDescription, Literal("Universal Journal ACDOCA & Basic Functions", lang="en")))
    g.add((comp_fi_gl_gl, SAP.parentComponent, comp_fi_gl))

    # MM (Materials Management)
    comp_mm = URIRef("http://data.sap.com/support/component/MM")
    g.add((comp_mm, RDF.type, SAP.ApplicationComponent))
    g.add((comp_mm, SAP.componentCode, Literal("MM", datatype=XSD.string)))
    g.add((comp_mm, SAP.componentDescription, Literal("Materials Management", lang="en")))

    comp_mm_pur = URIRef("http://data.sap.com/support/component/MM-PUR")
    g.add((comp_mm_pur, RDF.type, SAP.ApplicationComponent))
    g.add((comp_mm_pur, SAP.componentCode, Literal("MM-PUR", datatype=XSD.string)))
    g.add((comp_mm_pur, SAP.componentDescription, Literal("Purchasing", lang="en")))
    g.add((comp_mm_pur, SAP.parentComponent, comp_mm))

    comp_mm_pur_po = URIRef("http://data.sap.com/support/component/MM-PUR-PO")
    g.add((comp_mm_pur_po, RDF.type, SAP.ApplicationComponent))
    g.add((comp_mm_pur_po, SAP.componentCode, Literal("MM-PUR-PO", datatype=XSD.string)))
    g.add((comp_mm_pur_po, SAP.componentDescription, Literal("Purchase Orders", lang="en")))
    g.add((comp_mm_pur_po, SAP.parentComponent, comp_mm_pur))

    # SD (Sales & Distribution)
    comp_sd = URIRef("http://data.sap.com/support/component/SD")
    g.add((comp_sd, RDF.type, SAP.ApplicationComponent))
    g.add((comp_sd, SAP.componentCode, Literal("SD", datatype=XSD.string)))
    g.add((comp_sd, SAP.componentDescription, Literal("Sales and Distribution", lang="en")))

    comp_sd_sls = URIRef("http://data.sap.com/support/component/SD-SLS")
    g.add((comp_sd_sls, RDF.type, SAP.ApplicationComponent))
    g.add((comp_sd_sls, SAP.componentCode, Literal("SD-SLS", datatype=XSD.string)))
    g.add((comp_sd_sls, SAP.componentDescription, Literal("Sales", lang="en")))
    g.add((comp_sd_sls, SAP.parentComponent, comp_sd))

    # -------------------------------------------------------------
    # 5. SimCat Taxonomies
    # -------------------------------------------------------------
    simcat_perf = URIRef("http://data.sap.com/support/simcat/PERFORMANCE")
    g.add((simcat_perf, RDF.type, SAP.SimCatCategory))
    g.add((simcat_perf, SAP.categoryName, Literal("Performance and Resource Contention", datatype=XSD.string)))

    simcat_dump = URIRef("http://data.sap.com/support/simcat/ABAP_DUMP")
    g.add((simcat_dump, RDF.type, SAP.SimCatCategory))
    g.add((simcat_dump, SAP.categoryName, Literal("Runtime ABAP Dump or Crash", datatype=XSD.string)))

    simcat_db = URIRef("http://data.sap.com/support/simcat/DATABASE_ERROR")
    g.add((simcat_db, RDF.type, SAP.SimCatCategory))
    g.add((simcat_db, SAP.categoryName, Literal("Database Connection and Execution Failure", datatype=XSD.string)))

    simcat_config = URIRef("http://data.sap.com/support/simcat/CONFIGURATION")
    g.add((simcat_config, RDF.type, SAP.SimCatCategory))
    g.add((simcat_config, SAP.categoryName, Literal("Customizing and Configuration Inconsistency", datatype=XSD.string)))

    # -------------------------------------------------------------
    # 6. System Alerts (Runtime ABAP Dumps and Telemetry)
    # -------------------------------------------------------------
    alert_timeout = URIRef("http://data.sap.com/support/alert/ALERT_TIME_OUT")
    g.add((alert_timeout, RDF.type, SAP.SystemAlert))
    g.add((alert_timeout, SAP.alertCode, Literal("TIME_OUT", datatype=XSD.string)))
    g.add((alert_timeout, SAP.severity, Literal("CRITICAL", datatype=XSD.string)))
    g.add((alert_timeout, SAP.affectsComponent, comp_bc_cst))
    g.add((alert_timeout, SAP.classifiedUnderSimCat, simcat_dump))
    g.add((alert_timeout, RDFS.label, Literal("ABAP Short Dump: Maximum runtime exceeded (TIME_OUT)", lang="en")))

    alert_tsv = URIRef("http://data.sap.com/support/alert/ALERT_TSV_PAGE_FAILED")
    g.add((alert_tsv, RDF.type, SAP.SystemAlert))
    g.add((alert_tsv, SAP.alertCode, Literal("TSV_TNEW_PAGE_ALLOC_FAILED", datatype=XSD.string)))
    g.add((alert_tsv, SAP.severity, Literal("CRITICAL", datatype=XSD.string)))
    g.add((alert_tsv, SAP.affectsComponent, comp_bc_cst_mm))
    g.add((alert_tsv, SAP.classifiedUnderSimCat, simcat_perf))
    g.add((alert_tsv, RDFS.label, Literal("Memory allocation failure: TSV_TNEW_PAGE_ALLOC_FAILED", lang="en")))

    alert_dbsql = URIRef("http://data.sap.com/support/alert/ALERT_DBSQL_NO_CONN")
    g.add((alert_dbsql, RDF.type, SAP.SystemAlert))
    g.add((alert_dbsql, SAP.alertCode, Literal("DBSQL_NO_MORE_CONNECTION", datatype=XSD.string)))
    g.add((alert_dbsql, SAP.severity, Literal("ERROR", datatype=XSD.string)))
    g.add((alert_dbsql, SAP.affectsComponent, comp_bc_db_hdb))
    g.add((alert_dbsql, SAP.classifiedUnderSimCat, simcat_db))
    g.add((alert_dbsql, RDFS.label, Literal("Database connection pool exhausted (DBSQL_NO_MORE_CONNECTION)", lang="en")))

    alert_opensql = URIRef("http://data.sap.com/support/alert/ALERT_CX_SY_OPEN_SQL")
    g.add((alert_opensql, RDF.type, SAP.SystemAlert))
    g.add((alert_opensql, SAP.alertCode, Literal("CX_SY_OPEN_SQL_ERROR", datatype=XSD.string)))
    g.add((alert_opensql, SAP.severity, Literal("ERROR", datatype=XSD.string)))
    g.add((alert_opensql, SAP.affectsComponent, comp_bc_db))
    g.add((alert_opensql, SAP.classifiedUnderSimCat, simcat_db))

    alert_fn_not_found = URIRef("http://data.sap.com/support/alert/ALERT_CALL_FN_NOT_FOUND")
    g.add((alert_fn_not_found, RDF.type, SAP.SystemAlert))
    g.add((alert_fn_not_found, SAP.alertCode, Literal("CALL_FUNCTION_NOT_FOUND", datatype=XSD.string)))
    g.add((alert_fn_not_found, SAP.severity, Literal("ERROR", datatype=XSD.string)))
    g.add((alert_fn_not_found, SAP.affectsComponent, comp_bc))
    g.add((alert_fn_not_found, SAP.classifiedUnderSimCat, simcat_dump))

    # -------------------------------------------------------------
    # 7. Help Documentation
    # -------------------------------------------------------------
    doc_mm_guide = URIRef("http://data.sap.com/support/doc/DOC_MEMORY_CONFIG")
    g.add((doc_mm_guide, RDF.type, SAP.HelpDocumentation))
    g.add((doc_mm_guide, RDFS.label, Literal("SAP S/4HANA Memory Management Configuration Guide", lang="en")))
    g.add((doc_mm_guide, SAP.docUri, Literal("https://help.sap.com/docs/s4hana_memory_mgmt", datatype=XSD.anyURI)))

    doc_acdoca = URIRef("http://data.sap.com/support/doc/DOC_ACDOCA_ARCH")
    g.add((doc_acdoca, RDF.type, SAP.HelpDocumentation))
    g.add((doc_acdoca, RDFS.label, Literal("Universal Journal ACDOCA Architecture & Partitioning", lang="en")))
    g.add((doc_acdoca, SAP.docUri, Literal("https://help.sap.com/docs/s4hana_acdoca_perf", datatype=XSD.anyURI)))

    # -------------------------------------------------------------
    # 8. SAP Notes (Synthesizing Multi-Hop & Prerequisite Chains)
    # -------------------------------------------------------------
    # Chain 1: Note 3012445 (Root Prereq) -> Note 3098110 (Intermediate) -> Note 3109922 (Target Solution)
    note_3012445 = URIRef("http://data.sap.com/support/note/3012445")
    g.add((note_3012445, RDF.type, SAP.SAPNote))
    g.add((note_3012445, SAP.noteNumber, Literal("3012445", datatype=XSD.string)))
    g.add((note_3012445, SAP.title, Literal("Core memory parameter configuration for HANA 2.0 SPS07", lang="en")))
    g.add((note_3012445, SAP.priority, Literal("High", datatype=XSD.string)))
    g.add((note_3012445, SAP.affectsComponent, comp_bc_cst_mm))
    g.add((note_3012445, SAP.validForComponentVersion, scv_basis_758))
    g.add((note_3012445, SAP.validForProductVersion, pv_s4_2023))
    g.add((note_3012445, SAP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3012445, SAP.maxSupportPackage, Literal(3, datatype=XSD.integer)))
    g.add((note_3012445, SAP.symptom, Literal("Suboptimal default heap limits causing early work process restarts.", lang="en")))
    g.add((note_3012445, SAP.rootCause, Literal("Conservative legacy buffer allocation profile parameters.", lang="en")))
    g.add((note_3012445, SAP.resolution, Literal("Apply updated profile parameters em/initial_size_MB and ztta/roll_extension.", lang="en")))
    g.add((note_3012445, SAP.referencedDocumentation, doc_mm_guide))

    note_3098110 = URIRef("http://data.sap.com/support/note/3098110")
    g.add((note_3098110, RDF.type, SAP.SAPNote))
    g.add((note_3098110, SAP.noteNumber, Literal("3098110", datatype=XSD.string)))
    g.add((note_3098110, SAP.title, Literal("Memory paging buffer expansion in SAP_BASIS 758", lang="en")))
    g.add((note_3098110, SAP.priority, Literal("Very High", datatype=XSD.string)))
    g.add((note_3098110, SAP.affectsComponent, comp_bc_cst_mm))
    g.add((note_3098110, SAP.validForComponentVersion, scv_basis_758))
    g.add((note_3098110, SAP.validForProductVersion, pv_s4_2023))
    g.add((note_3098110, SAP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3098110, SAP.maxSupportPackage, Literal(2, datatype=XSD.integer)))
    g.add((note_3098110, SAP.hasPrerequisiteNote, note_3012445))
    g.add((note_3098110, SAP.symptom, Literal("Paging area exhaustion under concurrent analytics reporting.", lang="en")))
    g.add((note_3098110, SAP.resolution, Literal("Implement kernel patch and adjust abap/heaplimit.", lang="en")))

    note_3109922 = URIRef("http://data.sap.com/support/note/3109922")
    g.add((note_3109922, RDF.type, SAP.SAPNote))
    g.add((note_3109922, SAP.noteNumber, Literal("3109922", datatype=XSD.string)))
    g.add((note_3109922, SAP.title, Literal("Memory allocation dump TSV_TNEW_PAGE_ALLOC_FAILED in ACDOCA reporting on S/4HANA 2023", lang="en")))
    g.add((note_3109922, SAP.priority, Literal("Very High", datatype=XSD.string)))
    g.add((note_3109922, SAP.affectsComponent, comp_fi_gl_gl))
    g.add((note_3109922, SAP.affectsComponent, comp_bc_cst_mm))
    g.add((note_3109922, SAP.resolvesAlert, alert_tsv))
    g.add((note_3109922, SAP.validForComponentVersion, scv_basis_758))
    g.add((note_3109922, SAP.validForProductVersion, pv_s4_2023))
    g.add((note_3109922, SAP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3109922, SAP.maxSupportPackage, Literal(2, datatype=XSD.integer)))
    g.add((note_3109922, SAP.hasPrerequisiteNote, note_3098110))
    g.add((note_3109922, SAP.classifiedUnderSimCat, simcat_perf))
    g.add((note_3109922, SAP.symptom, Literal("Universal Journal ACDOCA financial extraction triggers dump TSV_TNEW_PAGE_ALLOC_FAILED during year-end closing.", lang="en")))
    g.add((note_3109922, SAP.rootCause, Literal("Unbounded internal table accumulation in FAGL_ACCOUNT_ITEMS extractor.", lang="en")))
    g.add((note_3109922, SAP.resolution, Literal("Implement cursor-based chunking logic and apply prerequisite Note 3098110.", lang="en")))
    g.add((note_3109922, SAP.referencedDocumentation, doc_acdoca))

    # Chain 2: Note 3185002 -> Note 3201440 (Resolves TIME_OUT on Purchase Order processing)
    note_3185002 = URIRef("http://data.sap.com/support/note/3185002")
    g.add((note_3185002, RDF.type, SAP.SAPNote))
    g.add((note_3185002, SAP.noteNumber, Literal("3185002", datatype=XSD.string)))
    g.add((note_3185002, SAP.title, Literal("Dispatcher queue optimization for asynchronous update tasks", lang="en")))
    g.add((note_3185002, SAP.priority, Literal("High", datatype=XSD.string)))
    g.add((note_3185002, SAP.affectsComponent, comp_bc_cst))
    g.add((note_3185002, SAP.validForComponentVersion, scv_basis_758))
    g.add((note_3185002, SAP.validForProductVersion, pv_s4_2023))
    g.add((note_3185002, SAP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3185002, SAP.maxSupportPackage, Literal(3, datatype=XSD.integer)))

    note_3201440 = URIRef("http://data.sap.com/support/note/3201440")
    g.add((note_3201440, RDF.type, SAP.SAPNote))
    g.add((note_3201440, SAP.noteNumber, Literal("3201440", datatype=XSD.string)))
    g.add((note_3201440, SAP.title, Literal("DUMP_SYSTEM_TIME_OUT during high-volume Purchase Order processing", lang="en")))
    g.add((note_3201440, SAP.priority, Literal("High", datatype=XSD.string)))
    g.add((note_3201440, SAP.affectsComponent, comp_mm_pur_po))
    g.add((note_3201440, SAP.resolvesAlert, alert_timeout))
    g.add((note_3201440, SAP.validForComponentVersion, scv_s4core_108))
    g.add((note_3201440, SAP.validForProductVersion, pv_s4_2023))
    g.add((note_3201440, SAP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3201440, SAP.maxSupportPackage, Literal(1, datatype=XSD.integer)))
    g.add((note_3201440, SAP.hasPrerequisiteNote, note_3185002))
    g.add((note_3201440, SAP.symptom, Literal("BAPI_PO_CREATE1 triggers TIME_OUT dump when processing POs with >500 line items.", lang="en")))
    g.add((note_3201440, SAP.rootCause, Literal("Sequential lock checks on table EKPO leading to lock escalation and dialog timeout.", lang="en")))
    g.add((note_3201440, SAP.resolution, Literal("Refactor lock enqueue to batch mode and apply prerequisite Note 3185002.", lang="en")))

    # Note 3345100: Resolves DBSQL_NO_MORE_CONNECTION on HANA DB
    note_3345100 = URIRef("http://data.sap.com/support/note/3345100")
    g.add((note_3345100, RDF.type, SAP.SAPNote))
    g.add((note_3345100, SAP.noteNumber, Literal("3345100", datatype=XSD.string)))
    g.add((note_3345100, SAP.title, Literal("HANA connection leak DBSQL_NO_MORE_CONNECTION in multi-tenant environment", lang="en")))
    g.add((note_3345100, SAP.priority, Literal("Very High", datatype=XSD.string)))
    g.add((note_3345100, SAP.affectsComponent, comp_bc_db_hdb))
    g.add((note_3345100, SAP.resolvesAlert, alert_dbsql))
    g.add((note_3345100, SAP.validForComponentVersion, scv_basis_758))
    g.add((note_3345100, SAP.validForProductVersion, pv_s4_2023))
    g.add((note_3345100, SAP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3345100, SAP.maxSupportPackage, Literal(2, datatype=XSD.integer)))
    g.add((note_3345100, SAP.symptom, Literal("Intermittent DBSQL_NO_MORE_CONNECTION errors when secondary database connections fail to release.", lang="en")))
    g.add((note_3345100, SAP.resolution, Literal("Enable strict connection reclamation pool in DBSL.", lang="en")))

    # Additional diverse notes for robust benchmarking
    additional_notes = [
        ("2954112", "Oracle to HANA migration data conversion syntax error in S4CORE", "High", comp_bc_db, scv_s4core_108, pv_s4_2023, alert_opensql, 0, 1),
        ("2877120", "Missing RFC function interface in external tax computation", "Medium", comp_fi, scv_s4core_108, pv_s4_2023, alert_fn_not_found, 0, 2),
        ("3144890", "Sales order pricing condition lock contention during billing runs", "High", comp_sd_sls, scv_s4core_108, pv_s4_2023, alert_timeout, 1, 2),
        ("2765001", "NetWeaver 7.50 memory paging adjustment for background jobs", "Low", comp_bc_cst_mm, scv_basis_757, pv_s4_2022, alert_tsv, 0, 5),
        ("3221980", "Database deadlock in General Ledger posting on S/4HANA 2022", "Very High", comp_fi_gl, scv_s4core_108, pv_s4_2022, alert_opensql, 0, 3),
        ("3155700", "Purchasing contract release authorization bypass check", "Very High", comp_mm_pur, scv_s4core_108, pv_s4_2023, None, 0, 3),
        ("3088210", "SAP HANA secondary index rebuild performance degradation", "Medium", comp_bc_db_hdb, scv_basis_758, pv_s4_2023, alert_timeout, 0, 2),
        ("3299100", "Universal Journal ACDOCA currency translation precision mismatch", "High", comp_fi_gl_gl, scv_s4core_108, pv_s4_2023, None, 1, 3),
    ]

    for note_num, title, priority, comp, scv, pv, alert, min_sp, max_sp in additional_notes:
        n_uri = URIRef(f"http://data.sap.com/support/note/{note_num}")
        g.add((n_uri, RDF.type, SAP.SAPNote))
        g.add((n_uri, SAP.noteNumber, Literal(note_num, datatype=XSD.string)))
        g.add((n_uri, SAP.title, Literal(title, lang="en")))
        g.add((n_uri, SAP.priority, Literal(priority, datatype=XSD.string)))
        g.add((n_uri, SAP.affectsComponent, comp))
        g.add((n_uri, SAP.validForComponentVersion, scv))
        g.add((n_uri, SAP.validForProductVersion, pv))
        g.add((n_uri, SAP.minSupportPackage, Literal(min_sp, datatype=XSD.integer)))
        g.add((n_uri, SAP.maxSupportPackage, Literal(max_sp, datatype=XSD.integer)))
        if alert:
            g.add((n_uri, SAP.resolvesAlert, alert))

    return g


def export_default_graph(output_path: str | Path = "semantic/data/sap_support_graph.ttl") -> str:
    """Build and save the default SAP Enterprise Support Knowledge Graph."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    g = build_sap_support_graph()
    g.serialize(destination=str(out), format="turtle")
    return str(out)


if __name__ == "__main__":
    out_file = export_default_graph()
    print(f"Generated SAP Support Knowledge Graph at {out_file}")
