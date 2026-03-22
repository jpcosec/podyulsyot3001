import { useParams } from 'react-router-dom';
import { useJobTimeline } from '../../features/job-pipeline/api/useJobTimeline';
import { usePackageFiles } from '../../features/job-pipeline/api/usePackageFiles';
import { MissionSummaryCard } from '../../features/job-pipeline/components/MissionSummaryCard';
import { PipelineChecklist } from '../../features/job-pipeline/components/PipelineChecklist';
import { PackageFileList } from '../../features/job-pipeline/components/PackageFileList';
import { DeploymentCta } from '../../features/job-pipeline/components/DeploymentCta';
import { Spinner } from '../../components/atoms/Spinner';

export function PackageDeployment() {
  const { source, jobId } = useParams<{ source: string; jobId: string }>();
  const timelineQuery = useJobTimeline(source!, jobId!);
  const filesQuery = usePackageFiles(source!, jobId!);

  if (timelineQuery.isLoading || filesQuery.isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner size="md" />
      </div>
    );
  }

  if (timelineQuery.isError || filesQuery.isError || !timelineQuery.data || !filesQuery.data) {
    return (
      <div className="p-6">
        <p className="font-mono text-error text-sm">DEPLOYMENT_DATA_NOT_FOUND</p>
      </div>
    );
  }

  const timeline = timelineQuery.data;
  const { files } = filesQuery.data;
  const isComplete = timeline.status === 'completed';
  const allApproved = timeline.stages.every(s => s.status === 'approved' || s.status === 'pending');

  return (
    <div className="overflow-auto p-6">
      <div className="max-w-3xl mx-auto space-y-6">
        <div>
          <h1 className="font-headline font-black text-2xl uppercase tracking-tighter text-primary drop-shadow-[0_0_12px_rgba(0,242,255,0.5)]">
            MISSION_COMPLETE
          </h1>
          <p className="font-mono text-[10px] text-on-muted mt-1 uppercase tracking-widest">
            {source} / {jobId}
          </p>
        </div>

        <MissionSummaryCard timeline={timeline} />
        <PipelineChecklist stages={timeline.stages} />
        {files.length > 0 && <PackageFileList files={files} />}
        <DeploymentCta source={source!} jobId={jobId!} isComplete={isComplete || allApproved} />
      </div>
    </div>
  );
}
