import { useState } from "react";
import axios from "axios";
import {
  LayoutDashboard,
  FileText,
  BarChart3,
  ShieldCheck,
  Settings,
  Upload,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock3,
  Search,
  Menu,
  X,
  TrendingUp,
  Activity,
  FileCheck2,
  Eye,
  ArrowLeft,
  Code2,
} from "lucide-react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [documents, setDocuments] = useState([]);
  const [file, setFile] = useState(null);
  const [documentType, setDocumentType] = useState("invoice");
  const [result, setResult] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [activePage, setActivePage] = useState("Dashboard");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showRawJson, setShowRawJson] = useState(false);

  async function loadDocuments() {
    try {
      const response = await axios.get(
        API_URL + "/api/v1/documents"
      );

      setDocuments(response.data.documents || []);
    } catch (error) {
      console.log("Could not load documents:", error);
    }
  }

  async function processDocument() {
    if (!file) {
      setError("Please select a document first.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    const formData = new FormData();

    formData.append("file", file);
    formData.append("document_type", documentType);

    try {
      const response = await axios.post(
        API_URL + "/api/v1/documents/process",
        formData
      );

      setResult(response.data);
      await loadDocuments();
    } catch (error) {
      console.log(error);

      if (error.response?.status === 429) {
        setError(
          "AI quota temporarily exceeded. Please try again later."
        );
      } else if (error.response?.data?.detail) {
        const detail = error.response.data.detail;

        if (typeof detail === "object") {
          setError(
            detail.message || "Document processing failed."
          );
        } else {
          setError(detail);
        }
      } else {
        setError("Document processing failed.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function openDocument(documentName) {
    try {
      setError("");

      const response = await axios.get(
        API_URL +
          "/api/v1/documents/" +
          encodeURIComponent(documentName)
      );

      setSelectedDocument(response.data);
      setShowRawJson(false);
    } catch (error) {
      console.log(error);
      setError("Could not load document details.");
    }
  }

  function closeDocument() {
    setSelectedDocument(null);
    setShowRawJson(false);
  }

  const successfulDocuments = documents.filter(
    function (document) {
      return document.processing_status === "PASS";
    }
  ).length;

  const failedDocuments = documents.filter(
    function (document) {
      return document.processing_status === "FAILED";
    }
  ).length;

  const validationReady = documents.filter(
    function (document) {
      return (
        document.processing_status === "PASS" &&
        document.validation?.checks?.length > 0
      );
    }
  ).length;

  const averageProcessingTime =
    documents.length > 0
      ? Math.round(
          documents.reduce(
            function (total, document) {
              return (
                total +
                (document.processing_metadata
                  ?.processing_time_ms || 0)
              );
            },
            0
          ) / documents.length
        )
      : 0;

  const documentTypeCounts = {
    invoice: documents.filter(
      function (document) {
        return document.document_type === "invoice";
      }
    ).length,

    balance_sheet: documents.filter(
      function (document) {
        return document.document_type === "balance_sheet";
      }
    ).length,

    profit_and_loss: documents.filter(
      function (document) {
        return document.document_type === "profit_and_loss";
      }
    ).length,

    cash_flow_statement: documents.filter(
      function (document) {
        return document.document_type === "cash_flow_statement";
      }
    ).length,
  };

  const maxTypeCount = Math.max(
    documentTypeCounts.invoice,
    documentTypeCounts.balance_sheet,
    documentTypeCounts.profit_and_loss,
    documentTypeCounts.cash_flow_statement,
    1
  );

  const filteredDocuments = documents.filter(
    function (document) {
      const searchText = search.toLowerCase();

      return (
        document.document_name
          ?.toLowerCase()
          .includes(searchText) ||
        document.document_type
          ?.toLowerCase()
          .includes(searchText)
      );
    }
  );

  function selectPage(page) {
    setActivePage(page);
    setSidebarOpen(false);
    setSelectedDocument(null);
  }

  function getDocumentTypeLabel(type) {
    const labels = {
      invoice: "Invoice",
      balance_sheet: "Balance Sheet",
      profit_and_loss: "Profit & Loss",
      cash_flow_statement: "Cash Flow",
    };

    return labels[type] || type;
  }

  function getStatusClass(status) {
    if (status === "PASS") {
      return "status-badge success";
    }

    if (status === "FAILED" || status === "FAIL") {
      return "status-badge failed";
    }

    return "status-badge neutral";
  }

  function renderSidebar() {
    return (
      <aside
        className={
          sidebarOpen
            ? "sidebar sidebar-open"
            : "sidebar"
        }
      >
        <div className="brand">
          <div className="brand-mark">N</div>

          <div>
            <h1>NEOSTATS</h1>
            <span>Document Intelligence</span>
          </div>

          <button
            className="mobile-close"
            onClick={function () {
              setSidebarOpen(false);
            }}
          >
            <X size={20} />
          </button>
        </div>

        <nav className="sidebar-nav">
          <p className="nav-title">MAIN MENU</p>

          <button
            className={
              activePage === "Dashboard"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={function () {
              selectPage("Dashboard");
            }}
          >
            <LayoutDashboard size={19} />
            <span>Dashboard</span>
          </button>

          <button
            className={
              activePage === "Documents"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={function () {
              selectPage("Documents");
            }}
          >
            <FileText size={19} />
            <span>Documents</span>
          </button>

          <button
            className={
              activePage === "Analytics"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={function () {
              selectPage("Analytics");
            }}
          >
            <BarChart3 size={19} />
            <span>Analytics</span>
          </button>

          <button
            className={
              activePage === "Validation"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={function () {
              selectPage("Validation");
            }}
          >
            <ShieldCheck size={19} />
            <span>Validation</span>
          </button>

          <p className="nav-title settings-title">
            SYSTEM
          </p>

          <button
            className={
              activePage === "Settings"
                ? "nav-item active"
                : "nav-item"
            }
            onClick={function () {
              selectPage("Settings");
            }}
          >
            <Settings size={19} />
            <span>Settings</span>
          </button>
        </nav>

        <div className="sidebar-bottom">
          <div className="system-status">
            <div className="status-dot"></div>

            <div>
              <strong>API Connected</strong>
              <span>System operational</span>
            </div>
          </div>
        </div>
      </aside>
    );
  }

  function renderTopbar() {
    return (
      <header className="topbar">
        <button
          className="mobile-menu"
          onClick={function () {
            setSidebarOpen(true);
          }}
        >
          <Menu size={22} />
        </button>

        <div className="page-heading">
          <h2>{activePage}</h2>

          <p>
            Monitor and manage your financial documents
          </p>
        </div>

        <div className="topbar-actions">
          <div className="search-box">
            <Search size={18} />

            <input
              type="text"
              placeholder="Search documents..."
              value={search}
              onChange={function (event) {
                setSearch(event.target.value);
              }}
            />
          </div>

          <button
            className="refresh-button"
            onClick={loadDocuments}
            title="Refresh documents"
          >
            <RefreshCw size={18} />
          </button>
        </div>
      </header>
    );
  }

  function renderDocumentDetails() {
    if (!selectedDocument) {
      return null;
    }

    const extractedFields =
      selectedDocument.extracted_data?.fields || {};

    const lineItems =
      selectedDocument.extracted_data?.line_items || [];

    const checks =
      selectedDocument.validation?.checks || [];

    return (
      <section className="document-detail-page">
        <div className="detail-header">
          <button
            className="refresh-action"
            onClick={closeDocument}
          >
            <ArrowLeft size={17} />
            Back to Documents
          </button>

          <div className="detail-title">
            <div className="detail-title-icon">
              <FileText size={25} />
            </div>

            <div>
              <h3>{selectedDocument.document_name}</h3>

              <p>
                {getDocumentTypeLabel(
                  selectedDocument.document_type
                )}
              </p>
            </div>
          </div>

          <span
            className={getStatusClass(
              selectedDocument.processing_status
            )}
          >
            {selectedDocument.processing_status ===
            "PASS" ? (
              <CheckCircle2 size={14} />
            ) : (
              <XCircle size={14} />
            )}

            {selectedDocument.processing_status}
          </span>
        </div>

        <div className="detail-stats">
          <div className="detail-stat">
            <span>Document Type</span>
            <strong>
              {getDocumentTypeLabel(
                selectedDocument.document_type
              )}
            </strong>
          </div>

          <div className="detail-stat">
            <span>File Type</span>
            <strong>
              {selectedDocument.file_validation
                ?.file_type || "-"}
            </strong>
          </div>

          <div className="detail-stat">
            <span>Pages</span>
            <strong>
              {selectedDocument.file_validation
                ?.page_count || "-"}
            </strong>
          </div>

          <div className="detail-stat">
            <span>Processing Time</span>
            <strong>
              {selectedDocument.processing_metadata
                ?.processing_time_ms || "-"}{" "}
              ms
            </strong>
          </div>
        </div>

        <section className="panel detail-panel">
          <div className="panel-header">
            <div>
              <h3>Extracted Information</h3>

              <p>
                Structured information extracted from the
                document
              </p>
            </div>
          </div>

          {Object.keys(extractedFields).length === 0 ? (
            <div className="empty-state">
              <FileText size={32} />

              <strong>No extracted fields</strong>

              <span>
                No structured fields were returned for
                this document.
              </span>
            </div>
          ) : (
            <div className="field-grid">
              {Object.entries(extractedFields).map(
                function ([key, field]) {
                  const value =
                    field?.value !== undefined
                      ? field.value
                      : field;

                  return (
                    <div
                      className="extracted-field"
                      key={key}
                    >
                      <span>
                        {key
                          .replaceAll("_", " ")
                          .replace(
                            /\b\w/g,
                            function (letter) {
                              return letter.toUpperCase();
                            }
                          )}
                      </span>

                      <strong>
                        {value === null ||
                        value === undefined ||
                        value === ""
                          ? "Not available"
                          : String(value)}
                      </strong>

                      {field?.source_text && (
                        <small>
                          Source: {field.source_text}
                        </small>
                      )}

                      {field?.page_number && (
                        <small>
                          Page: {field.page_number}
                        </small>
                      )}
                    </div>
                  );
                }
              )}
            </div>
          )}
        </section>

        <section className="panel detail-panel">
          <div className="panel-header">
            <div>
              <h3>Line Items / Financial Table</h3>

              <p>
                Structured table information extracted
                from the document
              </p>
            </div>
          </div>

          {lineItems.length === 0 ? (
            <div className="empty-state compact-empty">
              <FileCheck2 size={30} />

              <strong>No line items available</strong>

              <span>
                This document does not contain structured
                line items.
              </span>
            </div>
          ) : (
            <div className="document-table-wrapper">
              <table className="document-table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Line Total</th>
                    <th>Page</th>
                  </tr>
                </thead>

                <tbody>
                  {lineItems.map(function (
                    item,
                    index
                  ) {
                    return (
                      <tr key={index}>
                        <td>
                          {item.description || "-"}
                        </td>

                        <td>
                          {item.quantity ?? "-"}
                        </td>

                        <td>
                          {item.unit_price ?? "-"}
                        </td>

                        <td>
                          {item.line_total ?? "-"}
                        </td>

                        <td>
                          {item.page_number || "-"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="panel detail-panel">
          <div className="panel-header">
            <div>
              <h3>Financial Validation</h3>

              <p>
                Consistency checks calculated from
                extracted financial information
              </p>
            </div>
          </div>

          {checks.length === 0 ? (
            <div className="empty-state compact-empty">
              <ShieldCheck size={30} />

              <strong>No validation checks</strong>

              <span>
                No financial validation checks were
                generated.
              </span>
            </div>
          ) : (
            <div className="validation-detail-list">
              {checks.map(function (check, index) {
                return (
                  <div
                    className="validation-detail-row"
                    key={index}
                  >
                    <div>
                      <strong>{check.name}</strong>

                      <span>
                        Formula:{" "}
                        {check.formula || "-"}
                      </span>
                    </div>

                    <div className="validation-values">
                      {check.calculated_value !==
                        null &&
                        check.calculated_value !==
                          undefined && (
                          <span>
                            Calculated:{" "}
                            {check.calculated_value}
                          </span>
                        )}

                      {check.reported_value !== null &&
                        check.reported_value !==
                          undefined && (
                          <span>
                            Reported:{" "}
                            {check.reported_value}
                          </span>
                        )}

                      {check.variance !== null &&
                        check.variance !==
                          undefined && (
                          <span>
                            Variance: {check.variance}
                          </span>
                        )}
                    </div>

                    <span
                      className={
                        check.status === "PASS"
                          ? "status-badge success"
                          : check.status === "FAIL"
                          ? "status-badge failed"
                          : "status-badge neutral"
                      }
                    >
                      {check.status}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </section>

        <section className="panel detail-panel">
          <div className="panel-header">
            <div>
              <h3>Processing Metadata</h3>

              <p>
                Technical information about document
                processing
              </p>
            </div>
          </div>

          <div className="metadata-grid">
            <div>
              <span>OCR Used</span>

              <strong>
                {selectedDocument.processing_metadata
                  ?.ocr_used
                  ? "Yes"
                  : "No"}
              </strong>
            </div>

            <div>
              <span>Processed At</span>

              <strong>
                {selectedDocument.processing_metadata
                  ?.processed_at || "-"}
              </strong>
            </div>

            <div>
              <span>Processing Time</span>

              <strong>
                {selectedDocument.processing_metadata
                  ?.processing_time_ms || "-"}{" "}
                ms
              </strong>
            </div>

            <div>
              <span>Overall Confidence</span>

              <strong>
                {selectedDocument.overall_confidence ??
                  "Not provided"}
              </strong>
            </div>
          </div>
        </section>

        <section className="panel detail-panel raw-json-panel">
          <div className="panel-header">
            <div>
              <h3>Raw Structured JSON</h3>

              <p>
                Complete API response for this processed
                document
              </p>
            </div>

            <button
              className="refresh-action"
              onClick={function () {
                setShowRawJson(!showRawJson);
              }}
            >
              <Code2 size={17} />

              {showRawJson
                ? "Hide JSON"
                : "View Raw JSON"}
            </button>
          </div>

          {showRawJson && (
            <pre className="raw-json">
              {JSON.stringify(
                selectedDocument,
                null,
                2
              )}
            </pre>
          )}
        </section>
      </section>
    );
  }

  function renderDashboard() {
    return (
      <>
        <section className="welcome-section">
          <div>
            <p className="eyebrow">
              DOCUMENT INTELLIGENCE
            </p>

            <h3>Financial Document Overview</h3>

            <p>
              Extract, validate and manage financial
              documents with AI.
            </p>
          </div>

          <div className="welcome-icon">
            <FileText size={42} />
          </div>
        </section>

        <section className="stats-grid">
          <div className="metric-card">
            <div className="metric-icon blue">
              <FileText size={21} />
            </div>

            <div className="metric-content">
              <span>Total Documents</span>
              <strong>{documents.length}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon green">
              <CheckCircle2 size={21} />
            </div>

            <div className="metric-content">
              <span>Successfully Processed</span>
              <strong>{successfulDocuments}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon red">
              <XCircle size={21} />
            </div>

            <div className="metric-content">
              <span>Failed</span>
              <strong>{failedDocuments}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon purple">
              <Clock3 size={21} />
            </div>

            <div className="metric-content">
              <span>Avg. Processing Time</span>
              <strong>{averageProcessingTime} ms</strong>
            </div>
          </div>
        </section>

        <section className="dashboard-grid">
          <div className="panel documents-panel">
            <div className="panel-header">
              <div>
                <h3>Recent Documents</h3>

                <p>
                  Recently processed financial documents
                </p>
              </div>

              <button
                className="text-button"
                onClick={function () {
                  selectPage("Documents");
                }}
              >
                View all
              </button>
            </div>

            {filteredDocuments.length === 0 ? (
              <div className="empty-state">
                <FileText size={36} />

                <strong>No documents found</strong>

                <span>
                  Process a document to see it here.
                </span>
              </div>
            ) : (
              <div className="document-table-wrapper">
                <table className="document-table">
                  <thead>
                    <tr>
                      <th>Document</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Pages</th>
                      <th>Action</th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredDocuments
                      .slice(0, 6)
                      .map(function (document, index) {
                        return (
                          <tr
                            key={
                              document.document_name +
                              index
                            }
                          >
                            <td>
                              <div className="document-name">
                                <div className="file-icon">
                                  <FileText size={17} />
                                </div>

                                <span>
                                  {
                                    document.document_name
                                  }
                                </span>
                              </div>
                            </td>

                            <td>
                              <span className="type-badge">
                                {getDocumentTypeLabel(
                                  document.document_type
                                )}
                              </span>
                            </td>

                            <td>
                              <span
                                className={getStatusClass(
                                  document.processing_status
                                )}
                              >
                                {document.processing_status ===
                                "PASS" ? (
                                  <CheckCircle2
                                    size={14}
                                  />
                                ) : (
                                  <XCircle size={14} />
                                )}

                                {
                                  document.processing_status
                                }
                              </span>
                            </td>

                            <td>
                              {document.file_validation
                                ?.page_count || "-"}
                            </td>

                            <td>
                              <button
                                className="view-button"
                                onClick={function () {
                                  openDocument(
                                    document.document_name
                                  );
                                }}
                              >
                                <Eye size={15} />
                                View
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div className="panel quick-panel">
            <div className="panel-header">
              <div>
                <h3>Process Document</h3>

                <p>Start a new AI analysis</p>
              </div>

              <div className="upload-icon">
                <Upload size={20} />
              </div>
            </div>

            <div className="upload-area">
              <Upload size={28} />

              <strong>
                {file
                  ? file.name
                  : "Upload financial document"}
              </strong>

              <span>PDF, JPG or PNG</span>

              <label className="choose-file">
                Choose file

                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={function (event) {
                    setFile(
                      event.target.files[0] || null
                    );
                  }}
                />
              </label>
            </div>

            <label className="form-label">
              Document type
            </label>

            <select
              className="document-select"
              value={documentType}
              onChange={function (event) {
                setDocumentType(event.target.value);
              }}
            >
              <option value="invoice">Invoice</option>

              <option value="balance_sheet">
                Balance Sheet
              </option>

              <option value="profit_and_loss">
                Profit &amp; Loss
              </option>

              <option value="cash_flow_statement">
                Cash Flow Statement
              </option>
            </select>

            <button
              className="process-button"
              onClick={processDocument}
              disabled={loading}
            >
              {loading
                ? "Processing..."
                : "Process Document"}
            </button>

            {error && (
              <div className="quota-error">
                <XCircle size={17} />
                <span>{error}</span>
              </div>
            )}
          </div>
        </section>

        {result && (
          <section className="panel result-panel">
            <div className="panel-header">
              <div>
                <h3>Latest Processing Result</h3>

                <p>{result.document_name}</p>
              </div>

              <span className="status-badge success">
                <CheckCircle2 size={14} />
                {result.processing_status}
              </span>
            </div>

            <div className="result-metrics">
              <div>
                <span>Document Type</span>

                <strong>
                  {getDocumentTypeLabel(
                    result.document_type
                  )}
                </strong>
              </div>

              <div>
                <span>File Type</span>

                <strong>
                  {result.file_validation?.file_type ||
                    "-"}
                </strong>
              </div>

              <div>
                <span>Pages</span>

                <strong>
                  {result.file_validation?.page_count ||
                    "-"}
                </strong>
              </div>

              <div>
                <span>Processing Time</span>

                <strong>
                  {result.processing_metadata
                    ?.processing_time_ms || "-"}{" "}
                  ms
                </strong>
              </div>
            </div>

            <div className="validation-summary">
              <div className="validation-title">
                <ShieldCheck size={20} />

                <strong>Validation Checks</strong>
              </div>

              {result.validation?.checks?.length > 0 ? (
                result.validation.checks
                  .slice(0, 5)
                  .map(function (check, index) {
                    return (
                      <div
                        className="validation-row"
                        key={index}
                      >
                        <span>{check.name}</span>

                        <span
                          className={
                            check.status === "PASS"
                              ? "status-badge success"
                              : check.status === "FAIL"
                              ? "status-badge failed"
                              : "status-badge neutral"
                          }
                        >
                          {check.status}
                        </span>
                      </div>
                    );
                  })
              ) : (
                <p>
                  No validation checks available.
                </p>
              )}
            </div>

            <button
              className="process-button secondary-process"
              onClick={function () {
                openDocument(result.document_name);
              }}
            >
              <Eye size={17} />
              Open Full Result
            </button>
          </section>
        )}
      </>
    );
  }

  function renderDocuments() {
    return (
      <section className="panel full-panel">
        <div className="panel-header">
          <div>
            <h3>All Documents</h3>

            <p>
              Complete document processing history
            </p>
          </div>

          <button
            className="refresh-action"
            onClick={loadDocuments}
          >
            <RefreshCw size={17} />
            Refresh
          </button>
        </div>

        <div className="document-table-wrapper">
          <table className="document-table">
            <thead>
              <tr>
                <th>Document</th>
                <th>Type</th>
                <th>Status</th>
                <th>Pages</th>
                <th>Processing Time</th>
                <th>Action</th>
              </tr>
            </thead>

            <tbody>
              {filteredDocuments.map(function (
                document,
                index
              ) {
                return (
                  <tr
                    key={
                      document.document_name + index
                    }
                  >
                    <td>
                      <div className="document-name">
                        <div className="file-icon">
                          <FileText size={17} />
                        </div>

                        <span>
                          {document.document_name}
                        </span>
                      </div>
                    </td>

                    <td>
                      <span className="type-badge">
                        {getDocumentTypeLabel(
                          document.document_type
                        )}
                      </span>
                    </td>

                    <td>
                      <span
                        className={getStatusClass(
                          document.processing_status
                        )}
                      >
                        {document.processing_status}
                      </span>
                    </td>

                    <td>
                      {document.file_validation
                        ?.page_count || "-"}
                    </td>

                    <td>
                      <span className="time-cell">
                        <Clock3 size={14} />

                        {document.processing_metadata
                          ?.processing_time_ms ||
                          "-"}{" "}
                        ms
                      </span>
                    </td>

                    <td>
                      <button
                        className="view-button"
                        onClick={function () {
                          openDocument(
                            document.document_name
                          );
                        }}
                      >
                        <Eye size={15} />
                        View
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    );
  }

  function renderAnalytics() {
    return (
      <>
        <section className="welcome-section">
          <div>
            <p className="eyebrow">ANALYTICS</p>

            <h3>Document Processing Analytics</h3>

            <p>
              Monitor document volume, processing
              performance and validation readiness.
            </p>
          </div>

          <div className="welcome-icon">
            <TrendingUp size={42} />
          </div>
        </section>

        <section className="stats-grid">
          <div className="metric-card">
            <div className="metric-icon blue">
              <FileText size={21} />
            </div>

            <div className="metric-content">
              <span>Total Documents</span>
              <strong>{documents.length}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon green">
              <CheckCircle2 size={21} />
            </div>

            <div className="metric-content">
              <span>Success Rate</span>
              <strong>
                {documents.length > 0
                  ? Math.round(
                      (successfulDocuments /
                        documents.length) *
                        100
                    )
                  : 0}
                %
              </strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon purple">
              <FileCheck2 size={21} />
            </div>

            <div className="metric-content">
              <span>Validation Ready</span>
              <strong>{validationReady}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon blue">
              <Activity size={21} />
            </div>

            <div className="metric-content">
              <span>Avg. Processing</span>
              <strong>{averageProcessingTime} ms</strong>
            </div>
          </div>
        </section>

        <section className="analytics-grid">
          <div className="panel analytics-panel">
            <div className="panel-header">
              <div>
                <h3>Documents by Type</h3>

                <p>
                  Distribution of processed document
                  categories
                </p>
              </div>
            </div>

            <div className="chart-area">
              {[
                ["Invoice", documentTypeCounts.invoice],
                [
                  "Balance Sheet",
                  documentTypeCounts.balance_sheet,
                ],
                [
                  "Profit & Loss",
                  documentTypeCounts.profit_and_loss,
                ],
                [
                  "Cash Flow",
                  documentTypeCounts.cash_flow_statement,
                ],
              ].map(function (item) {
                return (
                  <div
                    className="chart-row"
                    key={item[0]}
                  >
                    <div className="chart-label">
                      <span>{item[0]}</span>
                      <strong>{item[1]}</strong>
                    </div>

                    <div className="bar-track">
                      <div
                        className="bar-fill"
                        style={{
                          width:
                            (item[1] /
                              maxTypeCount) *
                              100 +
                            "%",
                        }}
                      ></div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="panel analytics-panel">
            <div className="panel-header">
              <div>
                <h3>Processing Status</h3>

                <p>
                  Current processing outcome
                  distribution
                </p>
              </div>
            </div>

            <div className="status-overview">
              <div className="status-stat success-stat">
                <CheckCircle2 size={24} />

                <div>
                  <span>Successful</span>
                  <strong>
                    {successfulDocuments}
                  </strong>
                </div>
              </div>

              <div className="status-stat failed-stat">
                <XCircle size={24} />

                <div>
                  <span>Failed</span>
                  <strong>{failedDocuments}</strong>
                </div>
              </div>

              <div className="status-stat neutral-stat">
                <FileCheck2 size={24} />

                <div>
                  <span>Validation Ready</span>
                  <strong>{validationReady}</strong>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="panel analytics-panel recent-analytics">
          <div className="panel-header">
            <div>
              <h3>Processing Performance</h3>

              <p>
                Average time required to process stored
                documents
              </p>
            </div>

            <div className="performance-value">
              <Clock3 size={18} />

              <strong>
                {averageProcessingTime} ms
              </strong>
            </div>
          </div>

          <div className="performance-content">
            <div className="performance-icon">
              <Activity size={28} />
            </div>

            <div>
              <strong>AI processing performance</strong>

              <p>
                Processing time is calculated from the
                documents currently stored in the
                system.
              </p>
            </div>
          </div>
        </section>
      </>
    );
  }

  function renderValidation() {
    const allChecks = documents.flatMap(function (
      document
    ) {
      return document.validation?.checks || [];
    });

    const passedChecks = allChecks.filter(
      function (check) {
        return check.status === "PASS";
      }
    ).length;

    const failedChecks = allChecks.filter(
      function (check) {
        return check.status === "FAIL";
      }
    ).length;

    return (
      <>
        <section className="welcome-section">
          <div>
            <p className="eyebrow">
              FINANCIAL VALIDATION
            </p>

            <h3>Validation Center</h3>

            <p>
              Review financial consistency checks
              generated from processed documents.
            </p>
          </div>

          <div className="welcome-icon">
            <ShieldCheck size={42} />
          </div>
        </section>

        <section className="stats-grid">
          <div className="metric-card">
            <div className="metric-icon blue">
              <ShieldCheck size={21} />
            </div>

            <div className="metric-content">
              <span>Total Checks</span>
              <strong>{allChecks.length}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon green">
              <CheckCircle2 size={21} />
            </div>

            <div className="metric-content">
              <span>Passed Checks</span>
              <strong>{passedChecks}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon red">
              <XCircle size={21} />
            </div>

            <div className="metric-content">
              <span>Failed Checks</span>
              <strong>{failedChecks}</strong>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-icon purple">
              <FileCheck2 size={21} />
            </div>

            <div className="metric-content">
              <span>Documents Ready</span>
              <strong>{validationReady}</strong>
            </div>
          </div>
        </section>

        <section className="panel full-panel">
          <div className="panel-header">
            <div>
              <h3>Validation Summary</h3>

              <p>
                Validation information from processed
                documents
              </p>
            </div>
          </div>

          {documents.length === 0 ? (
            <div className="empty-state">
              <ShieldCheck size={36} />

              <strong>No validation data</strong>

              <span>
                Process a financial document to
                generate validation checks.
              </span>
            </div>
          ) : (
            <div className="document-table-wrapper">
              <table className="document-table">
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Type</th>
                    <th>Checks</th>
                    <th>Passed</th>
                    <th>Failed</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {documents.map(function (
                    document,
                    index
                  ) {
                    const checks =
                      document.validation?.checks ||
                      [];

                    const passed = checks.filter(
                      function (check) {
                        return check.status === "PASS";
                      }
                    ).length;

                    const failed = checks.filter(
                      function (check) {
                        return check.status === "FAIL";
                      }
                    ).length;

                    return (
                      <tr
                        key={
                          document.document_name +
                          index
                        }
                      >
                        <td>
                          <div className="document-name">
                            <div className="file-icon">
                              <ShieldCheck
                                size={17}
                              />
                            </div>

                            <span>
                              {
                                document.document_name
                              }
                            </span>
                          </div>
                        </td>

                        <td>
                          <span className="type-badge">
                            {getDocumentTypeLabel(
                              document.document_type
                            )}
                          </span>
                        </td>

                        <td>{checks.length}</td>

                        <td>
                          <span className="status-badge success">
                            {passed}
                          </span>
                        </td>

                        <td>
                          <span
                            className={
                              failed > 0
                                ? "status-badge failed"
                                : "status-badge neutral"
                            }
                          >
                            {failed}
                          </span>
                        </td>

                        <td>
                          <button
                            className="view-button"
                            onClick={function () {
                              openDocument(
                                document.document_name
                              );
                            }}
                          >
                            <Eye size={15} />
                            View
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </>
    );
  }

  function renderSettings() {
    return (
      <>
        <section className="welcome-section">
          <div>
            <p className="eyebrow">SYSTEM</p>

            <h3>Application Settings</h3>

            <p>
              Current configuration and service
              information.
            </p>
          </div>

          <div className="welcome-icon">
            <Settings size={42} />
          </div>
        </section>

        <section className="settings-grid">
          <div className="panel settings-card">
            <div className="settings-icon">
              <Activity size={22} />
            </div>

            <div>
              <h3>API Service</h3>

              <p>FastAPI backend service</p>

              <span className="status-badge success">
                <CheckCircle2 size={14} />
                Connected
              </span>
            </div>
          </div>

          <div className="panel settings-card">
            <div className="settings-icon">
              <FileText size={22} />
            </div>

            <div>
              <h3>Supported Documents</h3>

              <p>
                Invoice, Balance Sheet, Profit &amp;
                Loss and Cash Flow Statement
              </p>
            </div>
          </div>

          <div className="panel settings-card">
            <div className="settings-icon">
              <ShieldCheck size={22} />
            </div>

            <div>
              <h3>File Limits</h3>

              <p>PDF, JPG and PNG files</p>

              <p>Maximum 10 MB and 3 pages</p>
            </div>
          </div>

          <div className="panel settings-card">
            <div className="settings-icon">
              <DatabaseIcon />
            </div>

            <div>
              <h3>Document Storage</h3>

              <p>PostgreSQL persistence</p>

              <span className="status-badge success">
                <CheckCircle2 size={14} />
                Operational
              </span>
            </div>
          </div>
        </section>
      </>
    );
  }

  function DatabaseIcon() {
    return (
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <ellipse cx="12" cy="5" rx="8" ry="3" />
        <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5" />
        <path d="M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" />
      </svg>
    );
  }

  return (
    <div className="app-shell">
      {renderSidebar()}

      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={function () {
            setSidebarOpen(false);
          }}
        ></div>
      )}

      <div className="main-area">
        {renderTopbar()}

        <main className="dashboard-content">
          {selectedDocument
            ? renderDocumentDetails()
            : activePage === "Dashboard"
            ? renderDashboard()
            : activePage === "Documents"
            ? renderDocuments()
            : activePage === "Analytics"
            ? renderAnalytics()
            : activePage === "Validation"
            ? renderValidation()
            : renderSettings()}
        </main>

        <footer className="main-footer">
          <span>
            NEOSTATS Document Intelligence
          </span>

          <span>
            AI-powered financial document processing
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;