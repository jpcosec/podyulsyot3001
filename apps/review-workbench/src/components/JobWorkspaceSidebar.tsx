import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import { getEvidenceBank, getJobTimeline, getProfileSummary } from "../api/client";
import type { EvidenceBankPayload, JobTimeline, ProfileSummary } from "../types/models";

interface StageInfo {
  stage: string;
  status: string;
}

export function JobWorkspaceSidebar(): JSX.Element {
  const params = useParams();
  const location = useLocation();
  const source = params.source ?? "";
  const jobId = params.jobId ?? "";

  const [evidence, setEvidence] = useState<EvidenceBankPayload | null>(null);
  const [profile, setProfile] = useState<ProfileSummary | null>(null);
  const [timeline, setTimeline] = useState<JobTimeline | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!source || !jobId) return;
    Promise.all([
      getEvidenceBank(source, jobId).catch(() => null),
      getProfileSummary(source, jobId).catch(() => null),
      getJobTimeline(source, jobId).catch(() => null),
    ]).then(([ev, prof, tl]) => {
      setEvidence(ev);
      setProfile(prof);
      setTimeline(tl);
      setLoading(false);
    });
  }, [source, jobId]);

  const currentPath = location.pathname;
  const isActive = (path: string) => currentPath.startsWith(path);

  const statusClass = (status: string) => {
    if (status === "completed") return "job-sidebar-status-optimal";
    if (status === "pending_review") return "job-sidebar-status-warning";
    if (status === "failed") return "job-sidebar-status-error";
    return "job-sidebar-status-pending";
  };

  const stageDotClass = (status: string) => {
    if (status === "completed") return "stage-dot stage-dot-completed";
    if (status === "pending_review") return "stage-dot stage-dot-review";
    if (status === "failed") return "stage-dot stage-dot-failed";
    if (status === "running") return "stage-dot stage-dot-running";
    return "stage-dot stage-dot-pending";
  };

  const categoryClass = (cat: string) => {
    if (cat === "project") return "evidence-category evidence-category-project";
    if (cat === "education") return "evidence-category evidence-category-education";
    if (cat === "skill") return "evidence-category evidence-category-skill";
    if (cat === "experience") return "evidence-category evidence-category-experience";
    return "evidence-tag";
  };

  const navLink = (to: string, icon: string, label: string, exact?: boolean) => {
    const active = exact ? currentPath === to : currentPath.startsWith(to);
    return (
      <Link
        key={to}
        to={to}
        className={`job-sidebar-nav-link ${active ? "job-sidebar-nav-link-active" : ""}`}
      >
        <span className="material-symbols-outlined">{icon}</span>
        {label}
      </Link>
    );
  };

  return (
    <aside className="job-sidebar">
      {/* Header: job info */}
      <div className="job-sidebar-header">
        <div className="job-sidebar-job-info">
          <div className="job-sidebar-job-icon">
            <span className="material-symbols-outlined" style={{ color: "#99f7ff", fontSize: 18 }}>
              work
            </span>
          </div>
          <div className="job-sidebar-job-meta">
            <div className="job-sidebar-job-source">{source}</div>
            <div className="job-sidebar-job-id">#{jobId}</div>
            {timeline && (
              <span className={`job-sidebar-status ${statusClass(timeline.status)}`}>
                {timeline.current_node.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="job-sidebar-nav">
          <div className="job-sidebar-nav-label">Navigation</div>
          {navLink("/", "folder_special", "Portfolio", true)}
          {source && jobId && (
            <>
              {navLink(`/jobs/${source}/${jobId}`, "database", "Evidence Bank")}
              {navLink(`/jobs/${source}/${jobId}`, "account_tree", "Graph Explorer")}
              {navLink(`/jobs/${source}/${jobId}?view=view-2`, "text_fields", "Extraction")}
              {navLink(`/jobs/${source}/${jobId}?view=view-3`, "edit_document", "Documents")}
              {navLink(`/jobs/${source}/${jobId}/node-editor`, "hub", "Node Editor")}
              {navLink(`/jobs/${source}/${jobId}/deployment`, "send", "Deployment")}
            </>
          )}
        </nav>
      </div>

      {/* Scrollable body */}
      <div className="job-sidebar-body">
        {/* Profile summary */}
        {profile && (
          <div className="job-sidebar-section">
            <div className="job-sidebar-section-title">Profile Stats</div>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap", padding: "0 0 8px" }}>
              {profile.skills_count > 0 && (
                <span className="evidence-tag">{profile.skills_count} skills</span>
              )}
              {profile.projects_count > 0 && (
                <span className="evidence-tag">{profile.projects_count} projects</span>
              )}
              {profile.education_count > 0 && (
                <span className="evidence-tag">{profile.education_count} edu</span>
              )}
            </div>
          </div>
        )}

        {/* Evidence Bank */}
        <div className="job-sidebar-section">
          <div className="job-sidebar-section-title">Evidence Bank ({evidence?.items?.length ?? 0})</div>

          {loading ? (
            <>
              <div className="evidence-card-skeleton" />
              <div className="evidence-card-skeleton" />
            </>
          ) : evidence?.items && evidence.items.length > 0 ? (
            evidence.items.map((item) => (
              <div key={item.id} className="evidence-card">
                <div className="evidence-card-terminal-port" />
                <div className="evidence-card-header">
                  <span className="evidence-card-id">ID: {item.id}</span>
                  <span className={categoryClass(item.category)}>{item.category}</span>
                </div>
                <p className="evidence-card-title">{item.title}</p>
                {item.tags.length > 0 && (
                  <div className="evidence-card-tags">
                    {item.tags.slice(0, 4).map((tag) => (
                      <span key={tag} className="evidence-tag">{tag}</span>
                    ))}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="job-sidebar-empty">
              <div className="job-sidebar-empty-icon">
                <span className="material-symbols-outlined">inventory_2</span>
              </div>
              <p>No evidence entries found.</p>
              <p style={{ fontSize: 9, opacity: 0.5, marginTop: 4 }}>
                Profile evidence not yet extracted.
              </p>
            </div>
          )}
        </div>

        {/* Stage jump */}
        {timeline && (
          <div className="job-sidebar-section">
            <div className="job-sidebar-section-title">Stage Jump</div>
            <div className="stage-jump-list">
              {timeline.stages.map((s: StageInfo) => (
                <Link
                  key={s.stage}
                  to={`/jobs/${source}/${jobId}?view=outputs&stage=${s.stage}`}
                  className={`stage-jump-item ${
                    timeline.current_node === s.stage ? "stage-jump-item-active" : ""
                  } ${s.status === "completed" ? "stage-jump-item-completed" : ""} ${
                    s.status === "failed" ? "stage-jump-item-failed" : ""
                  }`}
                >
                  <span className={stageDotClass(s.status)} />
                  {s.stage.replace(/_/g, " ")}
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
}
