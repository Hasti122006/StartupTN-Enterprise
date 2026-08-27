import React from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Skeleton,
} from '@mui/material';
import {
  Business as CompanyIcon,
  PlayCircle as RunningIcon,
  Error as FailedIcon,
  Today as TodayIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
} from 'recharts';

interface SectorStat {
  sector: string;
  count: number;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export const DashboardPage: React.FC = () => {
  // Queries
  const { data: summary, isLoading: isSummaryLoading } = useQuery({
    queryKey: ['jobs-summary'],
    queryFn: async () => (await apiClient.get('/jobs/stats/summary')).data,
    refetchInterval: 5000,
  });

  const { data: dailyStats } = useQuery({
    queryKey: ['daily-stats'],
    queryFn: async () => (await apiClient.get('/companies/stats/daily')).data,
  });

  const { data: sectorStats } = useQuery<SectorStat[]>({
    queryKey: ['sector-stats'],
    queryFn: async () => (await apiClient.get('/companies/stats/sectors')).data,
  });

  const { data: stageStats } = useQuery({
    queryKey: ['stage-stats'],
    queryFn: async () => (await apiClient.get('/companies/stats/stages')).data,
  });

  const { data: recentJobs } = useQuery({
    queryKey: ['recent-jobs'],
    queryFn: async () => (await apiClient.get('/jobs/?page=1&page_size=5')).data,
  });

  const { data: scraperStatus } = useQuery({
    queryKey: ['scraper-status'],
    queryFn: async () => (await apiClient.get('/scraper/status')).data,
    refetchInterval: 3000,
  });

  const activeJob = scraperStatus?.active_job;

  const cardItems = [
    {
      title: 'Companies Scraped',
      value: summary?.total_companies ?? 0,
      icon: <CompanyIcon color="primary" sx={{ fontSize: 36 }} />,
      color: '#3b82f6',
    },
    {
      title: 'Running Jobs',
      value: summary?.running_jobs ?? 0,
      icon: <RunningIcon color="success" sx={{ fontSize: 36 }} />,
      color: '#10b981',
    },
    {
      title: 'Failed Jobs',
      value: summary?.failed_jobs ?? 0,
      icon: <FailedIcon color="error" sx={{ fontSize: 36 }} />,
      color: '#ef4444',
    },
    {
      title: "Today's Jobs",
      value: summary?.today_jobs ?? 0,
      icon: <TodayIcon color="warning" sx={{ fontSize: 36 }} />,
      color: '#f59e0b',
    },
  ];

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Dashboard Overview
      </Typography>

      {/* Active Job Live Progress Banner */}
      {activeJob && (
        <Card sx={{ mb: 4, bgcolor: 'action.hover', border: '1px solid primary.main' }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1, alignItems: 'center' }}>
              <Typography variant="h6" color="primary">
                Active Job #{activeJob.id} — {activeJob.status.toUpperCase()}
              </Typography>

              <Chip
                label={`Page ${activeJob.current_page} / ${activeJob.total_pages || 'Auto'}`}
                color="primary"
                size="small"
              />
            </Box>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
              Current Company: <strong>{activeJob.current_company || 'Initialising page...'}</strong>
            </Typography>
            <LinearProgress
              variant="determinate"
              value={
                activeJob.total_pages > 0
                  ? Math.min((activeJob.current_page / activeJob.total_pages) * 100, 100)
                  : 50
              }
              sx={{ height: 10, borderRadius: 5 }}
            />
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {cardItems.map((card, idx) => (
          <Grid item xs={12} sm={6} md={3} key={idx}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Box
                  sx={{
                    p: 1.5,
                    borderRadius: 3,
                    bgcolor: `${card.color}15`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {card.icon}
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    {card.title}
                  </Typography>
                  {isSummaryLoading ? (
                    <Skeleton width={60} height={36} />
                  ) : (
                    <Typography variant="h4" sx={{ fontWeight: 700 }}>
                      {card.value}
                    </Typography>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Charts Section */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {/* Line Chart: Scraped Companies Trend */}
        <Grid item xs={12} md={7}>
          <Card sx={{ p: 2, height: 360 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Scrape Velocity (Last 7 Days)
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={dailyStats || []}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="date" />
                <YAxis />
                <RechartsTooltip />
                <Line
                  type="monotone"
                  dataKey="count"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  dot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Grid>

        {/* Pie Chart: Sector Distribution */}
        <Grid item xs={12} md={5}>
          <Card sx={{ p: 2, height: 360 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Top Sectors Breakdown
            </Typography>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={sectorStats || []}
                  dataKey="count"
                  nameKey="sector"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={(entry) => entry.sector}
                >
                  {(sectorStats || []).map((_: SectorStat, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Card>
        </Grid>

        {/* Bar Chart: Stage Breakdown */}
        <Grid item xs={12}>
          <Card sx={{ p: 2, height: 320 }}>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
              Companies by Funding / Development Stage
            </Typography>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={stageStats || []}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                <XAxis dataKey="stage" />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="count" fill="#10b981" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Jobs Table */}
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
        Recent Execution Jobs
      </Typography>
      <TableContainer component={Paper} sx={{ borderRadius: 3, border: 1, borderColor: 'divider' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Job ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Scraped / Failed</TableCell>
              <TableCell>Workers</TableCell>
              <TableCell>Start Time</TableCell>
              <TableCell>Duration</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(recentJobs?.items || []).map((job: any) => (
              <TableRow key={job.id} hover>
                <TableCell>#{job.id}</TableCell>
                <TableCell>
                  <Chip
                    label={job.status}
                    size="small"
                    color={
                      job.status === 'completed'
                        ? 'success'
                        : job.status === 'running'
                        ? 'primary'
                        : job.status === 'failed'
                        ? 'error'
                        : 'warning'
                    }
                  />
                </TableCell>
                <TableCell>
                  {job.scraped_companies} / {job.failed_companies}
                </TableCell>
                <TableCell>{job.workers}</TableCell>
                <TableCell>
                  {job.start_time ? new Date(job.start_time).toLocaleString() : '-'}
                </TableCell>
                <TableCell>{job.duration ? `${job.duration}s` : '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
