"""Deterministic generator for high-fidelity SAP Enterprise Support Knowledge Graph.

Synthesizes interconnected multi-source RDF data:
- PPMS product and software lifecycle hierarchy
- Application component taxonomies
- System alerts and ABAP runtime dumps
- SimCat problem categories
- SAP Notes with symptoms, resolutions, and prerequisite dependency chains
- Synthetic Help Documentation references
"""

from __future__ import annotations

from pathlib import Path

from rdflib import RDF, RDFS, XSD, Graph, Literal, Namespace, URIRef

_NAMESPACE_REGISTRY = {
    "cifsup": "https://example.org/cifre-kg/support#",
    "cifppms": "https://example.org/cifre-kg/ppms#",
    "cifdata": "https://example.org/cifre-kg/data/",
    "ciferp": "https://example.org/cifre-kg/erp#",
    "cifskos": "https://example.org/cifre-kg/vocabulary#",
    "cifmeta": "https://example.org/cifre-kg/meta#",
    "cifmetaid": "https://example.org/cifre-kg/id/meta/",
}

CIFSUP = Namespace(_NAMESPACE_REGISTRY["cifsup"])
CIFPPMS = Namespace(_NAMESPACE_REGISTRY["cifppms"])
CIFDATA = Namespace(_NAMESPACE_REGISTRY["cifdata"])
CIFERP = Namespace(_NAMESPACE_REGISTRY["ciferp"])
CIFSKOS = Namespace(_NAMESPACE_REGISTRY["cifskos"])
CIFMETA = Namespace(_NAMESPACE_REGISTRY["cifmeta"])
CIFMETAID = Namespace(_NAMESPACE_REGISTRY["cifmetaid"])


def build_sap_support_graph(ontology_paths: list[str | Path] | None = None) -> Graph:
    """Build and populate the SAP Enterprise Support Knowledge Graph."""
    g = Graph()
    g.bind("cifsup", CIFSUP)
    g.bind("cifppms", CIFPPMS)
    g.bind("cifdata", CIFDATA)
    g.bind("ciferp", CIFERP)
    g.bind("cifskos", CIFSKOS)
    g.bind("cifmeta", CIFMETA)
    g.bind("cifmetaid", CIFMETAID)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("xsd", XSD)

    metadata = CIFMETAID["dataset-cifre-synthetic-support-ppms-v1"]
    g.add((metadata, RDF.type, CIFMETA.SyntheticDataset))
    g.add((metadata, CIFMETA.datasetId, Literal("cifre-synthetic-support-ppms-v1")))
    g.add((metadata, CIFMETA.sourceKind, Literal("synthetic_fixture")))
    g.add((metadata, CIFMETA.authority, Literal("independent_repository")))
    g.add((metadata, CIFMETA.official, Literal(False)))
    g.add((metadata, CIFMETA.generatedBy, Literal("src/semantic_layer/kg/sap_dataset_generator.py:build_sap_support_graph")))
    g.add((metadata, CIFMETA.graphPath, Literal("semantic/data/sap_support_graph.ttl")))

    # Load base ontologies if provided
    if ontology_paths:
        for p in ontology_paths:
            g.parse(location=str(p), format="turtle")

    # -------------------------------------------------------------
    # 1. PPMS Product Line & Products
    # -------------------------------------------------------------
    pl_s4 = URIRef("https://example.org/cifre-kg/data/ppms/productline/S4HANA")
    g.add((pl_s4, RDF.type, CIFPPMS.ProductLine))
    g.add((pl_s4, RDFS.label, Literal("SAP S/4HANA Product Line", lang="en")))
    g.add((pl_s4, CIFPPMS.productLineCode, Literal("S4HANA", datatype=XSD.string)))

    pl_nw = URIRef("https://example.org/cifre-kg/data/ppms/productline/NETWEAVER")
    g.add((pl_nw, RDF.type, CIFPPMS.ProductLine))
    g.add((pl_nw, RDFS.label, Literal("SAP NetWeaver Platform", lang="en")))
    g.add((pl_nw, CIFPPMS.productLineCode, Literal("NETWEAVER", datatype=XSD.string)))

    prod_s4_onprem = URIRef("https://example.org/cifre-kg/data/ppms/product/S4HANA_ONPREM")
    g.add((prod_s4_onprem, RDF.type, CIFPPMS.Product))
    g.add((prod_s4_onprem, RDFS.label, Literal("SAP S/4HANA On-Premise", lang="en")))
    g.add((prod_s4_onprem, CIFPPMS.belongsToProductLine, pl_s4))
    g.add((prod_s4_onprem, CIFPPMS.productCode, Literal("S4HANA_ONPREM", datatype=XSD.string)))

    prod_nw_abap = URIRef("https://example.org/cifre-kg/data/ppms/product/NW_ABAP")
    g.add((prod_nw_abap, RDF.type, CIFPPMS.Product))
    g.add((prod_nw_abap, RDFS.label, Literal("SAP NetWeaver Application Server ABAP", lang="en")))
    g.add((prod_nw_abap, CIFPPMS.belongsToProductLine, pl_nw))

    # -------------------------------------------------------------
    # 2. PPMS Software Components
    # -------------------------------------------------------------
    sc_basis = URIRef("https://example.org/cifre-kg/data/ppms/component/SAP_BASIS")
    g.add((sc_basis, RDF.type, CIFPPMS.SoftwareComponent))
    g.add((sc_basis, RDFS.label, Literal("SAP Basis Component (System Infrastructure)", lang="en")))
    g.add((sc_basis, CIFPPMS.componentName, Literal("SAP_BASIS", datatype=XSD.string)))

    sc_s4core = URIRef("https://example.org/cifre-kg/data/ppms/component/S4CORE")
    g.add((sc_s4core, RDF.type, CIFPPMS.SoftwareComponent))
    g.add((sc_s4core, RDFS.label, Literal("S/4HANA Core Application Logic", lang="en")))
    g.add((sc_s4core, CIFPPMS.componentName, Literal("S4CORE", datatype=XSD.string)))

    sc_appl = URIRef("https://example.org/cifre-kg/data/ppms/component/SAP_APPL")
    g.add((sc_appl, RDF.type, CIFPPMS.SoftwareComponent))
    g.add((sc_appl, RDFS.label, Literal("SAP Logistics and Accounting Core", lang="en")))
    g.add((sc_appl, CIFPPMS.componentName, Literal("SAP_APPL", datatype=XSD.string)))

    # -------------------------------------------------------------
    # 3. PPMS Product Versions & Component Versions
    # -------------------------------------------------------------
    # S/4HANA 2023
    pv_s4_2023 = URIRef("https://example.org/cifre-kg/data/ppms/version/S4HANA_2023")
    g.add((pv_s4_2023, RDF.type, CIFPPMS.ProductVersion))
    g.add((pv_s4_2023, RDFS.label, Literal("SAP S/4HANA 2023 Release", lang="en")))
    g.add((pv_s4_2023, CIFPPMS.versionCode, Literal("S4HANA_2023", datatype=XSD.string)))
    g.add((pv_s4_2023, CIFPPMS.releaseYear, Literal(2023, datatype=XSD.integer)))
    g.add((prod_s4_onprem, CIFPPMS.hasProductVersion, pv_s4_2023))

    scv_basis_758 = URIRef("https://example.org/cifre-kg/data/ppms/compversion/SAP_BASIS_758")
    g.add((scv_basis_758, RDF.type, CIFPPMS.SoftwareComponentVersion))
    g.add((scv_basis_758, RDFS.label, Literal("SAP_BASIS 758", lang="en")))
    g.add((scv_basis_758, CIFPPMS.componentVersionString, Literal("758", datatype=XSD.string)))
    g.add((scv_basis_758, CIFPPMS.isVersionOfComponent, sc_basis))
    g.add((pv_s4_2023, CIFPPMS.includesComponent, scv_basis_758))

    scv_s4core_108 = URIRef("https://example.org/cifre-kg/data/ppms/compversion/S4CORE_108")
    g.add((scv_s4core_108, RDF.type, CIFPPMS.SoftwareComponentVersion))
    g.add((scv_s4core_108, RDFS.label, Literal("S4CORE 108", lang="en")))
    g.add((scv_s4core_108, CIFPPMS.componentVersionString, Literal("108", datatype=XSD.string)))
    g.add((scv_s4core_108, CIFPPMS.isVersionOfComponent, sc_s4core))
    g.add((pv_s4_2023, CIFPPMS.includesComponent, scv_s4core_108))

    # S/4HANA 2022
    pv_s4_2022 = URIRef("https://example.org/cifre-kg/data/ppms/version/S4HANA_2022")
    g.add((pv_s4_2022, RDF.type, CIFPPMS.ProductVersion))
    g.add((pv_s4_2022, RDFS.label, Literal("SAP S/4HANA 2022 Release", lang="en")))
    g.add((pv_s4_2022, CIFPPMS.versionCode, Literal("S4HANA_2022", datatype=XSD.string)))
    g.add((pv_s4_2022, CIFPPMS.releaseYear, Literal(2022, datatype=XSD.integer)))
    g.add((prod_s4_onprem, CIFPPMS.hasProductVersion, pv_s4_2022))

    scv_basis_757 = URIRef("https://example.org/cifre-kg/data/ppms/compversion/SAP_BASIS_757")
    g.add((scv_basis_757, RDF.type, CIFPPMS.SoftwareComponentVersion))
    g.add((scv_basis_757, RDFS.label, Literal("SAP_BASIS 757", lang="en")))
    g.add((scv_basis_757, CIFPPMS.componentVersionString, Literal("757", datatype=XSD.string)))
    g.add((scv_basis_757, CIFPPMS.isVersionOfComponent, sc_basis))
    g.add((pv_s4_2022, CIFPPMS.includesComponent, scv_basis_757))

    # Support Packages for SAP_BASIS 758 (SP00, SP01, SP02, SP03)
    for sp_level in range(4):
        sp_uri = URIRef(f"https://example.org/cifre-kg/data/ppms/sp/SAP_BASIS_758_SP{sp_level:02d}")
        g.add((sp_uri, RDF.type, CIFPPMS.SupportPackage))
        g.add((sp_uri, RDFS.label, Literal(f"SAP_BASIS 758 SP{sp_level:02d}", lang="en")))
        g.add((sp_uri, CIFPPMS.stackLevel, Literal(sp_level, datatype=XSD.integer)))
        g.add((sp_uri, CIFPPMS.spName, Literal(f"SP{sp_level:02d}", datatype=XSD.string)))
        g.add((scv_basis_758, CIFPPMS.hasSupportPackage, sp_uri))

    # -------------------------------------------------------------
    # 4. Application Components Hierarchy
    # -------------------------------------------------------------
    # BC (Basis)
    comp_bc = URIRef("https://example.org/cifre-kg/data/support/component/BC")
    g.add((comp_bc, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_bc, CIFSUP.componentCode, Literal("BC", datatype=XSD.string)))
    g.add((comp_bc, CIFSUP.componentDescription, Literal("Basis Components", lang="en")))

    comp_bc_db = URIRef("https://example.org/cifre-kg/data/support/component/BC-DB")
    g.add((comp_bc_db, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_bc_db, CIFSUP.componentCode, Literal("BC-DB", datatype=XSD.string)))
    g.add((comp_bc_db, CIFSUP.componentDescription, Literal("Database Interface and Infrastructure", lang="en")))
    g.add((comp_bc_db, CIFSUP.parentComponent, comp_bc))

    comp_bc_db_hdb = URIRef("https://example.org/cifre-kg/data/support/component/BC-DB-HDB")
    g.add((comp_bc_db_hdb, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_bc_db_hdb, CIFSUP.componentCode, Literal("BC-DB-HDB", datatype=XSD.string)))
    g.add((comp_bc_db_hdb, CIFSUP.componentDescription, Literal("SAP HANA Database Interface", lang="en")))
    g.add((comp_bc_db_hdb, CIFSUP.parentComponent, comp_bc_db))

    comp_bc_cst = URIRef("https://example.org/cifre-kg/data/support/component/BC-CST")
    g.add((comp_bc_cst, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_bc_cst, CIFSUP.componentCode, Literal("BC-CST", datatype=XSD.string)))
    g.add((comp_bc_cst, CIFSUP.componentDescription, Literal("Client Server Technology", lang="en")))
    g.add((comp_bc_cst, CIFSUP.parentComponent, comp_bc))

    comp_bc_cst_mm = URIRef("https://example.org/cifre-kg/data/support/component/BC-CST-MM")
    g.add((comp_bc_cst_mm, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_bc_cst_mm, CIFSUP.componentCode, Literal("BC-CST-MM", datatype=XSD.string)))
    g.add((comp_bc_cst_mm, CIFSUP.componentDescription, Literal("Memory Management & Work Processes", lang="en")))
    g.add((comp_bc_cst_mm, CIFSUP.parentComponent, comp_bc_cst))

    # FI (Financials)
    comp_fi = URIRef("https://example.org/cifre-kg/data/support/component/FI")
    g.add((comp_fi, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_fi, CIFSUP.componentCode, Literal("FI", datatype=XSD.string)))
    g.add((comp_fi, CIFSUP.componentDescription, Literal("Financial Accounting", lang="en")))

    comp_fi_gl = URIRef("https://example.org/cifre-kg/data/support/component/FI-GL")
    g.add((comp_fi_gl, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_fi_gl, CIFSUP.componentCode, Literal("FI-GL", datatype=XSD.string)))
    g.add((comp_fi_gl, CIFSUP.componentDescription, Literal("General Ledger Accounting", lang="en")))
    g.add((comp_fi_gl, CIFSUP.parentComponent, comp_fi))

    comp_fi_gl_gl = URIRef("https://example.org/cifre-kg/data/support/component/FI-GL-GL")
    g.add((comp_fi_gl_gl, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_fi_gl_gl, CIFSUP.componentCode, Literal("FI-GL-GL", datatype=XSD.string)))
    g.add((comp_fi_gl_gl, CIFSUP.componentDescription, Literal("Universal Journal ACDOCA & Basic Functions", lang="en")))
    g.add((comp_fi_gl_gl, CIFSUP.parentComponent, comp_fi_gl))

    # MM (Materials Management)
    comp_mm = URIRef("https://example.org/cifre-kg/data/support/component/MM")
    g.add((comp_mm, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_mm, CIFSUP.componentCode, Literal("MM", datatype=XSD.string)))
    g.add((comp_mm, CIFSUP.componentDescription, Literal("Materials Management", lang="en")))

    comp_mm_pur = URIRef("https://example.org/cifre-kg/data/support/component/MM-PUR")
    g.add((comp_mm_pur, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_mm_pur, CIFSUP.componentCode, Literal("MM-PUR", datatype=XSD.string)))
    g.add((comp_mm_pur, CIFSUP.componentDescription, Literal("Purchasing", lang="en")))
    g.add((comp_mm_pur, CIFSUP.parentComponent, comp_mm))

    comp_mm_pur_po = URIRef("https://example.org/cifre-kg/data/support/component/MM-PUR-PO")
    g.add((comp_mm_pur_po, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_mm_pur_po, CIFSUP.componentCode, Literal("MM-PUR-PO", datatype=XSD.string)))
    g.add((comp_mm_pur_po, CIFSUP.componentDescription, Literal("Purchase Orders", lang="en")))
    g.add((comp_mm_pur_po, CIFSUP.parentComponent, comp_mm_pur))

    # SD (Sales & Distribution)
    comp_sd = URIRef("https://example.org/cifre-kg/data/support/component/SD")
    g.add((comp_sd, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_sd, CIFSUP.componentCode, Literal("SD", datatype=XSD.string)))
    g.add((comp_sd, CIFSUP.componentDescription, Literal("Sales and Distribution", lang="en")))

    comp_sd_sls = URIRef("https://example.org/cifre-kg/data/support/component/SD-SLS")
    g.add((comp_sd_sls, RDF.type, CIFSUP.ApplicationComponent))
    g.add((comp_sd_sls, CIFSUP.componentCode, Literal("SD-SLS", datatype=XSD.string)))
    g.add((comp_sd_sls, CIFSUP.componentDescription, Literal("Sales", lang="en")))
    g.add((comp_sd_sls, CIFSUP.parentComponent, comp_sd))

    # -------------------------------------------------------------
    # 5. SimCat Taxonomies
    # -------------------------------------------------------------
    simcat_perf = URIRef("https://example.org/cifre-kg/data/support/simcat/PERFORMANCE")
    g.add((simcat_perf, RDF.type, CIFSUP.SimCatCategory))
    g.add((simcat_perf, CIFSUP.categoryName, Literal("Performance and Resource Contention", lang="en")))

    simcat_dump = URIRef("https://example.org/cifre-kg/data/support/simcat/ABAP_DUMP")
    g.add((simcat_dump, RDF.type, CIFSUP.SimCatCategory))
    g.add((simcat_dump, CIFSUP.categoryName, Literal("Runtime ABAP Dump or Crash", lang="en")))

    simcat_db = URIRef("https://example.org/cifre-kg/data/support/simcat/DATABASE_ERROR")
    g.add((simcat_db, RDF.type, CIFSUP.SimCatCategory))
    g.add((simcat_db, CIFSUP.categoryName, Literal("Database Connection and Execution Failure", lang="en")))

    simcat_config = URIRef("https://example.org/cifre-kg/data/support/simcat/CONFIGURATION")
    g.add((simcat_config, RDF.type, CIFSUP.SimCatCategory))
    g.add((simcat_config, CIFSUP.categoryName, Literal("Customizing and Configuration Inconsistency", lang="en")))

    # -------------------------------------------------------------
    # 6. System Alerts (Runtime ABAP Dumps and Telemetry)
    # -------------------------------------------------------------
    alert_timeout = URIRef("https://example.org/cifre-kg/data/support/alert/ALERT_TIME_OUT")
    g.add((alert_timeout, RDF.type, CIFSUP.SystemAlert))
    g.add((alert_timeout, CIFSUP.alertCode, Literal("TIME_OUT", datatype=XSD.string)))
    g.add((alert_timeout, CIFSUP.severity, Literal("CRITICAL", datatype=XSD.string)))
    g.add((alert_timeout, CIFSUP.affectsComponent, comp_bc_cst))
    g.add((alert_timeout, CIFSUP.classifiedUnderSimCat, simcat_dump))
    g.add((alert_timeout, RDFS.label, Literal("ABAP Short Dump: Maximum runtime exceeded (TIME_OUT)", lang="en")))

    alert_tsv = URIRef("https://example.org/cifre-kg/data/support/alert/ALERT_TSV_PAGE_FAILED")
    g.add((alert_tsv, RDF.type, CIFSUP.SystemAlert))
    g.add((alert_tsv, CIFSUP.alertCode, Literal("TSV_TNEW_PAGE_ALLOC_FAILED", datatype=XSD.string)))
    g.add((alert_tsv, CIFSUP.severity, Literal("CRITICAL", datatype=XSD.string)))
    g.add((alert_tsv, CIFSUP.affectsComponent, comp_bc_cst_mm))
    g.add((alert_tsv, CIFSUP.classifiedUnderSimCat, simcat_perf))
    g.add((alert_tsv, RDFS.label, Literal("Memory allocation failure: TSV_TNEW_PAGE_ALLOC_FAILED", lang="en")))

    alert_dbsql = URIRef("https://example.org/cifre-kg/data/support/alert/ALERT_DBSQL_NO_CONN")
    g.add((alert_dbsql, RDF.type, CIFSUP.SystemAlert))
    g.add((alert_dbsql, CIFSUP.alertCode, Literal("DBSQL_NO_MORE_CONNECTION", datatype=XSD.string)))
    g.add((alert_dbsql, CIFSUP.severity, Literal("ERROR", datatype=XSD.string)))
    g.add((alert_dbsql, CIFSUP.affectsComponent, comp_bc_db_hdb))
    g.add((alert_dbsql, CIFSUP.classifiedUnderSimCat, simcat_db))
    g.add((alert_dbsql, RDFS.label, Literal("Database connection pool exhausted (DBSQL_NO_MORE_CONNECTION)", lang="en")))

    alert_opensql = URIRef("https://example.org/cifre-kg/data/support/alert/ALERT_CX_SY_OPEN_SQL")
    g.add((alert_opensql, RDF.type, CIFSUP.SystemAlert))
    g.add((alert_opensql, CIFSUP.alertCode, Literal("CX_SY_OPEN_SQL_ERROR", datatype=XSD.string)))
    g.add((alert_opensql, CIFSUP.severity, Literal("ERROR", datatype=XSD.string)))
    g.add((alert_opensql, CIFSUP.affectsComponent, comp_bc_db))
    g.add((alert_opensql, CIFSUP.classifiedUnderSimCat, simcat_db))

    alert_fn_not_found = URIRef("https://example.org/cifre-kg/data/support/alert/ALERT_CALL_FN_NOT_FOUND")
    g.add((alert_fn_not_found, RDF.type, CIFSUP.SystemAlert))
    g.add((alert_fn_not_found, CIFSUP.alertCode, Literal("CALL_FUNCTION_NOT_FOUND", datatype=XSD.string)))
    g.add((alert_fn_not_found, CIFSUP.severity, Literal("ERROR", datatype=XSD.string)))
    g.add((alert_fn_not_found, CIFSUP.affectsComponent, comp_bc))
    g.add((alert_fn_not_found, CIFSUP.classifiedUnderSimCat, simcat_dump))

    # -------------------------------------------------------------
    # 7. Help Documentation
    # -------------------------------------------------------------
    doc_mm_guide = URIRef("https://example.org/cifre-kg/data/support/doc/DOC_MEMORY_CONFIG")
    g.add((doc_mm_guide, RDF.type, CIFSUP.HelpDocumentation))
    g.add((doc_mm_guide, RDFS.label, Literal("Synthetic Help Documentation: memory management configuration", lang="en")))
    g.add((doc_mm_guide, CIFSUP.docUri, Literal("https://example.org/cifre-kg/data/support/doc/s4hana_memory_mgmt", datatype=XSD.anyURI)))

    doc_acdoca = URIRef("https://example.org/cifre-kg/data/support/doc/DOC_ACDOCA_ARCH")
    g.add((doc_acdoca, RDF.type, CIFSUP.HelpDocumentation))
    g.add((doc_acdoca, RDFS.label, Literal("Synthetic Help Documentation: journal architecture and partitioning", lang="en")))
    g.add((doc_acdoca, CIFSUP.docUri, Literal("https://example.org/cifre-kg/data/support/doc/s4hana_acdoca_perf", datatype=XSD.anyURI)))

    # -------------------------------------------------------------
    # 8. SAP Notes (Synthesizing Multi-Hop & Prerequisite Chains)
    # -------------------------------------------------------------
    # Chain 1: Note 3012445 (Root Prereq) -> Note 3098110 (Intermediate) -> Note 3109922 (Target Solution)
    note_3012445 = URIRef("https://example.org/cifre-kg/data/support/note/3012445")
    g.add((note_3012445, RDF.type, CIFSUP.SAPNote))
    g.add((note_3012445, CIFSUP.noteNumber, Literal("3012445", datatype=XSD.string)))
    g.add((note_3012445, CIFSUP.title, Literal("Core memory parameter configuration for HANA 2.0 SPS07", lang="en")))
    g.add((note_3012445, CIFSUP.priority, Literal("High", datatype=XSD.string)))
    g.add((note_3012445, CIFSUP.affectsComponent, comp_bc_cst_mm))
    g.add((note_3012445, CIFSUP.validForComponentVersion, scv_basis_758))
    g.add((note_3012445, CIFSUP.validForProductVersion, pv_s4_2023))
    g.add((note_3012445, CIFSUP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3012445, CIFSUP.maxSupportPackage, Literal(3, datatype=XSD.integer)))
    g.add((note_3012445, CIFSUP.symptom, Literal("Suboptimal default heap limits causing early work process restarts.", lang="en")))
    g.add((note_3012445, CIFSUP.rootCause, Literal("Conservative legacy buffer allocation profile parameters.", lang="en")))
    g.add((note_3012445, CIFSUP.resolution, Literal("Apply updated profile parameters em/initial_size_MB and ztta/roll_extension.", lang="en")))
    g.add((note_3012445, CIFSUP.referencedDocumentation, doc_mm_guide))

    note_3098110 = URIRef("https://example.org/cifre-kg/data/support/note/3098110")
    g.add((note_3098110, RDF.type, CIFSUP.SAPNote))
    g.add((note_3098110, CIFSUP.noteNumber, Literal("3098110", datatype=XSD.string)))
    g.add((note_3098110, CIFSUP.title, Literal("Memory paging buffer expansion in SAP_BASIS 758", lang="en")))
    g.add((note_3098110, CIFSUP.priority, Literal("Very High", datatype=XSD.string)))
    g.add((note_3098110, CIFSUP.affectsComponent, comp_bc_cst_mm))
    g.add((note_3098110, CIFSUP.validForComponentVersion, scv_basis_758))
    g.add((note_3098110, CIFSUP.validForProductVersion, pv_s4_2023))
    g.add((note_3098110, CIFSUP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3098110, CIFSUP.maxSupportPackage, Literal(2, datatype=XSD.integer)))
    g.add((note_3098110, CIFSUP.hasPrerequisiteNote, note_3012445))
    g.add((note_3098110, CIFSUP.symptom, Literal("Paging area exhaustion under concurrent analytics reporting.", lang="en")))
    g.add((note_3098110, CIFSUP.resolution, Literal("Implement kernel patch and adjust abap/heaplimit.", lang="en")))

    note_3109922 = URIRef("https://example.org/cifre-kg/data/support/note/3109922")
    g.add((note_3109922, RDF.type, CIFSUP.SAPNote))
    g.add((note_3109922, CIFSUP.noteNumber, Literal("3109922", datatype=XSD.string)))
    g.add((note_3109922, CIFSUP.title, Literal("Memory allocation dump TSV_TNEW_PAGE_ALLOC_FAILED in ACDOCA reporting on S/4HANA 2023", lang="en")))
    g.add((note_3109922, CIFSUP.priority, Literal("Very High", datatype=XSD.string)))
    g.add((note_3109922, CIFSUP.affectsComponent, comp_fi_gl_gl))
    g.add((note_3109922, CIFSUP.affectsComponent, comp_bc_cst_mm))
    g.add((note_3109922, CIFSUP.resolvesAlert, alert_tsv))
    g.add((note_3109922, CIFSUP.validForComponentVersion, scv_basis_758))
    g.add((note_3109922, CIFSUP.validForProductVersion, pv_s4_2023))
    g.add((note_3109922, CIFSUP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3109922, CIFSUP.maxSupportPackage, Literal(2, datatype=XSD.integer)))
    g.add((note_3109922, CIFSUP.hasPrerequisiteNote, note_3098110))
    g.add((note_3109922, CIFSUP.classifiedUnderSimCat, simcat_perf))
    g.add((note_3109922, CIFSUP.symptom, Literal("Universal Journal ACDOCA financial extraction triggers dump TSV_TNEW_PAGE_ALLOC_FAILED during year-end closing.", lang="en")))
    g.add((note_3109922, CIFSUP.rootCause, Literal("Unbounded internal table accumulation in FAGL_ACCOUNT_ITEMS extractor.", lang="en")))
    g.add((note_3109922, CIFSUP.resolution, Literal("Implement cursor-based chunking logic and apply prerequisite Note 3098110.", lang="en")))
    g.add((note_3109922, CIFSUP.referencedDocumentation, doc_acdoca))

    # Chain 2: Note 3185002 -> Note 3201440 (Resolves TIME_OUT on Purchase Order processing)
    note_3185002 = URIRef("https://example.org/cifre-kg/data/support/note/3185002")
    g.add((note_3185002, RDF.type, CIFSUP.SAPNote))
    g.add((note_3185002, CIFSUP.noteNumber, Literal("3185002", datatype=XSD.string)))
    g.add((note_3185002, CIFSUP.title, Literal("Dispatcher queue optimization for asynchronous update tasks", lang="en")))
    g.add((note_3185002, CIFSUP.priority, Literal("High", datatype=XSD.string)))
    g.add((note_3185002, CIFSUP.affectsComponent, comp_bc_cst))
    g.add((note_3185002, CIFSUP.validForComponentVersion, scv_basis_758))
    g.add((note_3185002, CIFSUP.validForProductVersion, pv_s4_2023))
    g.add((note_3185002, CIFSUP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3185002, CIFSUP.maxSupportPackage, Literal(3, datatype=XSD.integer)))

    note_3201440 = URIRef("https://example.org/cifre-kg/data/support/note/3201440")
    g.add((note_3201440, RDF.type, CIFSUP.SAPNote))
    g.add((note_3201440, CIFSUP.noteNumber, Literal("3201440", datatype=XSD.string)))
    g.add((note_3201440, CIFSUP.title, Literal("DUMP_SYSTEM_TIME_OUT during high-volume Purchase Order processing", lang="en")))
    g.add((note_3201440, CIFSUP.priority, Literal("High", datatype=XSD.string)))
    g.add((note_3201440, CIFSUP.affectsComponent, comp_mm_pur_po))
    g.add((note_3201440, CIFSUP.resolvesAlert, alert_timeout))
    g.add((note_3201440, CIFSUP.validForComponentVersion, scv_s4core_108))
    g.add((note_3201440, CIFSUP.validForProductVersion, pv_s4_2023))
    g.add((note_3201440, CIFSUP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3201440, CIFSUP.maxSupportPackage, Literal(1, datatype=XSD.integer)))
    g.add((note_3201440, CIFSUP.hasPrerequisiteNote, note_3185002))
    g.add((note_3201440, CIFSUP.symptom, Literal("BAPI_PO_CREATE1 triggers TIME_OUT dump when processing POs with >500 line items.", lang="en")))
    g.add((note_3201440, CIFSUP.rootCause, Literal("Sequential lock checks on table EKPO leading to lock escalation and dialog timeout.", lang="en")))
    g.add((note_3201440, CIFSUP.resolution, Literal("Refactor lock enqueue to batch mode and apply prerequisite Note 3185002.", lang="en")))

    # Note 3345100: Resolves DBSQL_NO_MORE_CONNECTION on HANA DB
    note_3345100 = URIRef("https://example.org/cifre-kg/data/support/note/3345100")
    g.add((note_3345100, RDF.type, CIFSUP.SAPNote))
    g.add((note_3345100, CIFSUP.noteNumber, Literal("3345100", datatype=XSD.string)))
    g.add((note_3345100, CIFSUP.title, Literal("HANA connection leak DBSQL_NO_MORE_CONNECTION in multi-tenant environment", lang="en")))
    g.add((note_3345100, CIFSUP.priority, Literal("Very High", datatype=XSD.string)))
    g.add((note_3345100, CIFSUP.affectsComponent, comp_bc_db_hdb))
    g.add((note_3345100, CIFSUP.resolvesAlert, alert_dbsql))
    g.add((note_3345100, CIFSUP.validForComponentVersion, scv_basis_758))
    g.add((note_3345100, CIFSUP.validForProductVersion, pv_s4_2023))
    g.add((note_3345100, CIFSUP.minSupportPackage, Literal(0, datatype=XSD.integer)))
    g.add((note_3345100, CIFSUP.maxSupportPackage, Literal(2, datatype=XSD.integer)))
    g.add((note_3345100, CIFSUP.symptom, Literal("Intermittent DBSQL_NO_MORE_CONNECTION errors when secondary database connections fail to release.", lang="en")))
    g.add((note_3345100, CIFSUP.resolution, Literal("Enable strict connection reclamation pool in DBSL.", lang="en")))

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
        n_uri = URIRef(f"https://example.org/cifre-kg/data/support/note/{note_num}")
        g.add((n_uri, RDF.type, CIFSUP.SAPNote))
        g.add((n_uri, CIFSUP.noteNumber, Literal(note_num, datatype=XSD.string)))
        g.add((n_uri, CIFSUP.title, Literal(title, lang="en")))
        g.add((n_uri, CIFSUP.priority, Literal(priority, datatype=XSD.string)))
        g.add((n_uri, CIFSUP.affectsComponent, comp))
        g.add((n_uri, CIFSUP.validForComponentVersion, scv))
        g.add((n_uri, CIFSUP.validForProductVersion, pv))
        g.add((n_uri, CIFSUP.minSupportPackage, Literal(min_sp, datatype=XSD.integer)))
        g.add((n_uri, CIFSUP.maxSupportPackage, Literal(max_sp, datatype=XSD.integer)))
        if alert:
            g.add((n_uri, CIFSUP.resolvesAlert, alert))

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
