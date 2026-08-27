import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box, Typography, Card, Grid, TextField, Button, FormControlLabel,
  Switch, Slider, LinearProgress, Chip, Paper, Alert, Divider,
} from '@mui/material';
import {
  PlayArrow as StartIcon, Pause as PauseIcon,
  PlayCircleOutline as ResumeIcon, Stop as StopIcon,
  Settings as SettingsIcon, Terminal as TerminalIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';

const JOB_ID_KEY = 'scraper_active_job_id';
const saveJobId = (id: number | null) =>
  id != null ? sessionStorage.setItem(JOB_ID_KEY, String(id)) : sessionStorage.removeItem(JOB_ID_KEY);
const loadJobId = (): number | null => {
  const v = sessionStorage.getItem(JOB_ID_KEY);
  const n = v ? parseInt(v, 10) : NaN;
  return isNaN(n) ? null : n;
};

export const ScraperPage: React.FC = () => {
  const queryClient = useQueryClient();

  // Config
  const [testMode, setTestMode] = useState(true);
  const [companyLimit, setCompanyLimit] = useState<number>(5);
  const [startPage, setStartPage] = useState<number>(1);
  const [endPage, setEndPage] = useState<number>(0);
  const [workers, setWorkers] = useState<number>(2);
  const [delayMin, setDelayMin] = useState<number>(1.0);
  const [delayMax, setDelayMax] = useState<number>(3.0);
  const [retryCount, setRetryCount] = useState<number>(3);
  const [timeoutVal, setTimeoutVal] = useState<number>(30);
  const [headless, setHeadless] = useState<boolean>(true);
  const [outputExcel, setOutputExcel] = useState<boolean>(true);
  const [outputCsv, setOutputCsv] = useState<boolean>(true);
  const [outputDb, setOutputDb] = useState<boolean>(true);

  // Validation
  const [startPageError, setStartPageError] = useState<string | null>(null);
  const [endPageError, setEndPageError] = useState<string | null>(null);
  const [companyLimitError, setCompanyLimitError] = useState<string | null>(null);

  // Logs
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  // Live elapsed timer
  const [liveElapsed, setLiveElapsed] = useState<number | null>(null);
  const elapsedRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Persisted job id
  const [currentJobId, setCurrentJobId] = useState<number | null>(loadJobId);
  const updateJobId = useCallback((id: number | null) => {
    setCurrentJobId(id);
    saveJobId(id);
  }, []);

  // Poll status
  const { data: statusData } = useQuery({
    queryKey: ['scraper-status', currentJobId],
    queryFn: async () => {
      const url = currentJobId ? `/scraper/status?job_id=${currentJobId}` : '/scraper/status';
      return (await apiClient.get(url)).data;
    },
    refetchInterval: (q) => {
      const d = q.state.data;
      return (d?.is_running || d?.is_paused || d?.is_stopping) ? 1500 : 5000;
    },
  });

  const activeJob = statusData?.active_job;
  const serverStatus: string = activeJob?.status ?? statusData?.status ?? 'idle';

  const isRunning  = ['running','starting','pending','queued'].includes(serverStatus);
  const isPaused   = serverStatus === 'paused';
  const isStopping = serverStatus === 'stopping';
  const isStopped  = serverStatus === 'stopped' || serverStatus === 'cancelled';
  const isCompleted = serverStatus === 'completed';
  const isFailed   = serverStatus === 'failed';
  const isIdle     = serverStatus === 'idle';
  const isActive   = isRunning || isPaused || isStopping;

  const jobIdToUse = activeJob?.id ?? statusData?.job_id ?? currentJobId;

  // Sync job id from server
  useEffect(() => {
    if (statusData?.job_id && statusData.job_id !== currentJobId) {
      updateJobId(Number(statusData.job_id));
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [statusData?.job_id]);

  // Live elapsed timer
  useEffect(() => {
    if (elapsedRef.current) { clearInterval(elapsedRef.current); elapsedRef.current = null; }

    if (isActive) {
      const startStr = activeJob?.started_at ?? activeJob?.start_time ?? null;
      let base = startStr
        ? Math.max(0, Math.floor((Date.now() - new Date(startStr).getTime()) / 1000))
        : (statusData?.elapsed_seconds ?? 0);
      setLiveElapsed(base);
      elapsedRef.current = setInterval(() => setLiveElapsed(p => (p ?? 0) + 1), 1000);
    } else if (isCompleted || isStopped || isFailed) {
      setLiveElapsed(activeJob?.duration ?? statusData?.elapsed_seconds ?? null);
    } else {
      setLiveElapsed(null);
    }

    return () => { if (elapsedRef.current) { clearInterval(elapsedRef.current); elapsedRef.current = null; } };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [serverStatus, activeJob?.id]);

  const fmtElapsed = (s: number | null) => {
    if (s == null) return '--';
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
    if (h > 0) return `${h}h ${String(m).padStart(2,'0')}m ${String(sec).padStart(2,'0')}s`;
    if (m > 0) return `${m}m ${String(sec).padStart(2,'0')}s`;
    return `${sec}s`;
  };

  // Validation
  useEffect(() => {
    setStartPageError(!Number.isInteger(startPage) || startPage < 1 ? 'Must be >= 1' : null);
    setEndPageError(!Number.isInteger(endPage) || !(endPage === 0 || endPage >= startPage) ? 'Must be 0 or >= Start Page' : null);
    setCompanyLimitError(!Number.isInteger(companyLimit) || companyLimit < 0 ? 'Must be 0 or positive' : null);
  }, [startPage, endPage, companyLimit]);
  const hasErrors = !!(startPageError || endPageError || companyLimitError);

  // Estimate
  const estimateSecs = React.useMemo(() => {
    if (companyLimit > 0) return Math.ceil((companyLimit * 10) / Math.max(1, workers));
    if (endPage > 0) { const p = Math.max(0, endPage - startPage + 1); if (p > 0) return Math.ceil((p * 12 * 10) / Math.max(1, workers)); }
    return null;
  }, [startPage, endPage, companyLimit, workers]);
  const fmtSecs = (s: number | null) => { if (!s) return 'Calculating...'; const m = Math.floor(s/60), sec = s%60; return m > 0 ? `~${m}m ${sec}s` : `~${sec}s`; };

  // WebSocket
  useEffect(() => {
    if (!jobIdToUse) return;
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const wsBase = ((import.meta as any).env?.VITE_WS_BASE_URL || `${proto}://${window.location.host}`).replace(/\/+$/, '');
    const ws = new WebSocket(`${wsBase}/ws/logs?job_id=${jobIdToUse}`);
    ws.onmessage = (e) => {
      try {
        const p = JSON.parse(e.data);
        const ts = p.created_at ? new Date(p.created_at).toLocaleTimeString() : new Date().toLocaleTimeString();
        setLogs(prev => [...prev.slice(-400), `[${ts}] [${p.level || 'INFO'}] ${p.message}`]);
      } catch { setLogs(prev => [...prev.slice(-400), e.data]); }
    };
    return () => ws.close();
  }, [jobIdToUse]);
  useEffect(() => { logEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [logs]);

  // Progress
  const progress = (() => {
    if (isCompleted) return 100;
    if (activeJob?.progress > 0) return Math.min(activeJob.progress, 100);
    if (statusData?.progress > 0) return Math.min(statusData.progress, 100);
    const tp = activeJob?.total_pages ?? 0, cp = activeJob?.current_page ?? 0;
    if (tp > 0 && cp > 0) return Math.min((cp / tp) * 100, 100);
    const sc = activeJob?.scraped_companies ?? 0, lim = companyLimit > 0 ? companyLimit : (activeJob?.total_companies ?? 0);
    if (sc > 0 && lim > 0) return Math.min((sc / lim) * 100, 100);
    return isRunning ? 5 : 0;
  })();

  const chipColor: any = isRunning ? 'success' : isPaused ? 'warning' : isStopping ? 'warning' : isCompleted ? 'info' : isFailed ? 'error' : 'default';

  // Mutations
  const startMutation = useMutation({
    mutationFn: async () => (await apiClient.post('/scraper/start', {
      test_mode: testMode, company_limit: companyLimit, start_page: startPage,
      end_page: endPage, workers, delay_min: delayMin, delay_max: delayMax,
      retry_count: retryCount, timeout: timeoutVal, headless,
      output_excel: outputExcel, output_csv: outputCsv, output_database: outputDb,
    })).data,
    onSuccess: (data) => {
      const id = data?.job_id ?? data?.id;
      if (id != null) updateJobId(Number(id));
      setLogs([]);
      queryClient.invalidateQueries({ queryKey: ['scraper-status'] });
    },
  });
  const pauseMutation = useMutation({
    mutationFn: async () => (await apiClient.post(`/scraper/pause/${jobIdToUse}`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scraper-status'] }),
  });
  const resumeMutation = useMutation({
    mutationFn: async () => (await apiClient.post(`/scraper/resume/${jobIdToUse}`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scraper-status'] }),
  });
  const stopMutation = useMutation({
    mutationFn: async () => (await apiClient.post(`/scraper/stop/${jobIdToUse}`)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['scraper-status'] }),
  });

  // Button gates — purely from server status
  const canStart  = !isActive && !startMutation.isPending && !hasErrors;
  const canPause  = isRunning && !pauseMutation.isPending;
  const canResume = isPaused  && !resumeMutation.isPending;
  const canStop   = isActive  && !stopMutation.isPending;

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        StartupTN Scraper Control Center
      </Typography>

      {/* Control Buttons */}
      <Card sx={{ mb: 4, p: 2 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
          <Button id="btn-start" variant="contained" color="primary" size="large" startIcon={<StartIcon />}
            disabled={!canStart} onClick={() => !hasErrors && startMutation.mutate()}>
            {startMutation.isPending ? 'Starting...' : 'Start New Scrape'}
          </Button>
          <Button id="btn-pause" variant="contained" color="warning" size="large" startIcon={<PauseIcon />}
            disabled={!canPause} onClick={() => pauseMutation.mutate()}>
            {pauseMutation.isPending ? 'Pausing...' : 'Pause'}
          </Button>
          <Button id="btn-resume" variant="contained" color="info" size="large" startIcon={<ResumeIcon />}
            disabled={!canResume} onClick={() => resumeMutation.mutate()}>
            {resumeMutation.isPending ? 'Resuming...' : 'Resume'}
          </Button>
          <Button id="btn-stop" variant="contained" color="error" size="large" startIcon={<StopIcon />}
            disabled={!canStop} onClick={() => stopMutation.mutate()}>
            {isStopping || stopMutation.isPending ? 'Stopping...' : 'Stop'}
          </Button>
          {jobIdToUse && (
            <Chip label={`Job #${jobIdToUse}  ·  ${serverStatus.toUpperCase()}`}
              color={chipColor} sx={{ fontWeight: 700, ml: 'auto' }} />
          )}
        </Box>
        {startMutation.isError  && <Alert severity="error" sx={{ mt: 2 }}>{(startMutation.error  as any)?.response?.data?.detail || (startMutation.error  as any)?.message || 'Failed to start'}</Alert>}
        {pauseMutation.isError  && <Alert severity="error" sx={{ mt: 2 }}>{(pauseMutation.error  as any)?.response?.data?.detail || 'Failed to pause'}</Alert>}
        {resumeMutation.isError && <Alert severity="error" sx={{ mt: 2 }}>{(resumeMutation.error as any)?.response?.data?.detail || 'Failed to resume'}</Alert>}
        {stopMutation.isError   && <Alert severity="error" sx={{ mt: 2 }}>{(stopMutation.error   as any)?.response?.data?.detail || 'Failed to stop'}</Alert>}
      </Card>

      <Grid container spacing={4}>
        {/* Settings */}
        <Grid item xs={12} md={5}>
          <Card sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <SettingsIcon color="primary" />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>Scraper Configuration</Typography>
            </Box>
            <Divider sx={{ mb: 3 }} />
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField id="inp-start-page" label="Start Page" type="number" fullWidth inputProps={{ min: 1 }}
                  value={startPage} onChange={e => setStartPage(Math.max(1, Math.floor(Number(e.target.value)||1)))}
                  error={!!startPageError} helperText={startPageError||''} disabled={isActive} />
              </Grid>
              <Grid item xs={6}>
                <TextField id="inp-end-page" label="End Page (0=Auto)" type="number" fullWidth inputProps={{ min: 0 }}
                  value={endPage} onChange={e => setEndPage(Math.max(0, Math.floor(Number(e.target.value)||0)))}
                  error={!!endPageError} helperText={endPageError||''} disabled={isActive} />
              </Grid>
              <Grid item xs={12}>
                <Alert severity="info">StartupTN credentials are configured securely in the scraper container.</Alert>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel control={<Switch id="sw-test" checked={testMode} onChange={e=>setTestMode(e.target.checked)} disabled={isActive} />}
                  label="Test Mode (limits to Company Limit)" />
              </Grid>
              <Grid item xs={12}>
                <TextField id="inp-limit" label="Company Limit (0=no limit)" type="number" fullWidth inputProps={{ min: 0 }}
                  value={companyLimit} onChange={e => setCompanyLimit(Math.max(0, parseInt(e.target.value,10)||0))}
                  helperText={companyLimitError||'Number of companies to scrape'} error={!!companyLimitError} disabled={isActive} />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="body2" gutterBottom>Parallel Workers: <strong>{workers}</strong></Typography>
                <Slider id="sl-workers" value={workers} min={1} max={10} step={1}
                  onChange={(_,v)=>setWorkers(v as number)} disabled={isActive} valueLabelDisplay="auto" />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>Estimated Time</Typography>
                <Typography variant="body1">{fmtSecs(estimateSecs)}</Typography>
              </Grid>
              <Grid item xs={6}>
                <TextField id="inp-dmin" label="Min Delay (s)" type="number" fullWidth value={delayMin}
                  onChange={e=>setDelayMin(Number(e.target.value))} disabled={isActive} />
              </Grid>
              <Grid item xs={6}>
                <TextField id="inp-dmax" label="Max Delay (s)" type="number" fullWidth value={delayMax}
                  onChange={e=>setDelayMax(Number(e.target.value))} disabled={isActive} />
              </Grid>
              <Grid item xs={6}>
                <TextField id="inp-retry" label="Retry Count" type="number" fullWidth value={retryCount}
                  onChange={e=>setRetryCount(Number(e.target.value))} disabled={isActive} />
              </Grid>
              <Grid item xs={6}>
                <TextField id="inp-timeout" label="Timeout (s)" type="number" fullWidth value={timeoutVal}
                  onChange={e=>setTimeoutVal(Number(e.target.value))} disabled={isActive} />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel control={<Switch id="sw-headless" checked={headless} onChange={e=>setHeadless(e.target.checked)} disabled={isActive} />}
                  label="Headless Browser Mode" />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" sx={{ mt: 1, mb: 1, fontWeight: 600 }}>Output Destinations</Typography>
                <FormControlLabel control={<Switch id="sw-db" checked={outputDb} onChange={e=>setOutputDb(e.target.checked)} disabled={isActive} />} label="MySQL Database" />
                <FormControlLabel control={<Switch id="sw-excel" checked={outputExcel} onChange={e=>setOutputExcel(e.target.checked)} disabled={isActive} />} label="Excel (.xlsx)" />
                <FormControlLabel control={<Switch id="sw-csv" checked={outputCsv} onChange={e=>setOutputCsv(e.target.checked)} disabled={isActive} />} label="CSV" />
              </Grid>
            </Grid>
          </Card>
        </Grid>

        {/* Progress + Logs */}
        <Grid item xs={12} md={7}>
          <Card sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 2 }}>Job Execution Progress</Typography>
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Current Page</Typography>
                <Typography variant="h6">
                  {activeJob?.current_page ?? 0} / {activeJob?.total_pages || (isIdle ? '--' : 'Auto')}
                </Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Scraped</Typography>
                <Typography variant="h6" color="success.main">{activeJob?.scraped_companies ?? 0}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Failed</Typography>
                <Typography variant="h6" color="error.main">{activeJob?.failed_companies ?? 0}</Typography>
              </Grid>
              <Grid item xs={6} sm={3}>
                <Typography variant="caption" color="text.secondary">Elapsed</Typography>
                <Typography variant="h6" color={isActive ? 'success.main' : 'text.primary'}>
                  {liveElapsed != null ? fmtElapsed(liveElapsed) : (isIdle ? '--' : '0s')}
                </Typography>
              </Grid>
            </Grid>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Current Company: <strong>
                {activeJob?.current_company || (isActive ? 'Initializing...' : isCompleted ? 'Completed' : '--')}
              </strong>
            </Typography>
            <LinearProgress id="progress-bar" variant="determinate" value={progress} sx={{ height: 12, borderRadius: 6 }} />
            <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
              {progress.toFixed(1)}%
            </Typography>
          </Card>

          <Card sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              <TerminalIcon color="primary" />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>Live Log Stream</Typography>
              {jobIdToUse && <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto' }}>Job #{jobIdToUse}</Typography>}
            </Box>
            <Paper elevation={0} sx={{ p: 2, bgcolor: '#0f172a', color: '#38bdf8', fontFamily: 'monospace', fontSize: '0.82rem', height: 320, overflowY: 'auto', borderRadius: 2 }}>
              {logs.length === 0 ? (
                <Typography variant="body2" sx={{ opacity: 0.5, color: '#94a3b8' }}>
                  {jobIdToUse ? `Waiting for log stream from Job #${jobIdToUse}...` : 'Start a scrape job to see live logs here.'}
                </Typography>
              ) : logs.map((line, i) => (
                <Box key={i} sx={{ py: 0.15, color: line.includes('[ERROR]') ? '#f87171' : line.includes('[WARNING]') ? '#fb923c' : '#38bdf8' }}>
                  {line}
                </Box>
              ))}
              <div ref={logEndRef} />
            </Paper>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
