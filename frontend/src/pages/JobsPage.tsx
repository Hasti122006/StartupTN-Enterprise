import React, { useState } from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Pagination,
  Card,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from '@mui/material';
import { Delete as DeleteIcon, Visibility as ViewIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export const JobsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState<any | null>(null);
  const queryClient = useQueryClient();

  const { data } = useQuery({
    queryKey: ['jobs', page],
    queryFn: async () => (await apiClient.get(`/jobs/?page=${page}&page_size=15`)).data,
    refetchInterval: 5000,
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => await apiClient.delete(`/jobs/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  });

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Scraper Jobs History
      </Typography>

      <TableContainer component={Paper} sx={{ borderRadius: 3, border: 1, borderColor: 'divider' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Job ID</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Pages (Current/Total)</TableCell>
              <TableCell>Scraped Companies</TableCell>
              <TableCell>Failed Companies</TableCell>
              <TableCell>Workers</TableCell>
              <TableCell>Start Time</TableCell>
              <TableCell>Duration</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(data?.items || []).map((job: any) => (
              <TableRow key={job.id} hover>
                <TableCell>#{job.id}</TableCell>
                <TableCell>
                  <Chip
                    label={job.status.toUpperCase()}
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
                  {job.current_page} / {job.total_pages || 'Auto'}
                </TableCell>
                <TableCell>{job.scraped_companies}</TableCell>
                <TableCell>{job.failed_companies}</TableCell>
                <TableCell>{job.workers}</TableCell>
                <TableCell>{job.start_time ? new Date(job.start_time).toLocaleString() : '-'}</TableCell>
                <TableCell>{job.duration ? `${job.duration}s` : '-'}</TableCell>
                <TableCell align="right">
                  <IconButton color="primary" onClick={() => setSelectedJob(job)}>
                    <ViewIcon />
                  </IconButton>
                  <IconButton color="error" onClick={() => deleteMutation.mutate(job.id)}>
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination count={Math.ceil((data?.total || 0) / 15)} page={page} onChange={(_, p) => setPage(p)} color="primary" />
      </Box>

      {/* Details Dialog */}
      <Dialog open={Boolean(selectedJob)} onClose={() => setSelectedJob(null)} maxWidth="sm" fullWidth>
        {selectedJob && (
          <>
            <DialogTitle>Job #{selectedJob.id} Details & Execution History</DialogTitle>
            <DialogContent dividers>
              <Typography variant="body2" paragraph><strong>Status:</strong> {selectedJob.status?.toUpperCase()}</Typography>
              <Typography variant="body2" paragraph><strong>Records Found / Total:</strong> {selectedJob.total_companies || 0}</Typography>
              <Typography variant="body2" paragraph><strong>Created Records:</strong> {selectedJob.created_records || 0}</Typography>
              <Typography variant="body2" paragraph><strong>Updated Records:</strong> {selectedJob.updated_records || 0}</Typography>
              <Typography variant="body2" paragraph><strong>Skipped Records:</strong> {selectedJob.skipped_records || 0}</Typography>
              <Typography variant="body2" paragraph><strong>Failed Records:</strong> {selectedJob.failed_companies || 0}</Typography>
              {selectedJob.n8n_execution_id && (
                <Typography variant="body2" paragraph><strong>n8n Execution ID:</strong> {selectedJob.n8n_execution_id}</Typography>
              )}
              {selectedJob.prompt && (
                <Typography variant="body2" paragraph><strong>AI Prompt:</strong> {selectedJob.prompt}</Typography>
              )}
              {selectedJob.started_at && (
                <Typography variant="body2" paragraph><strong>Started At:</strong> {new Date(selectedJob.started_at).toLocaleString()}</Typography>
              )}
              {selectedJob.completed_at && (
                <Typography variant="body2" paragraph><strong>Completed At:</strong> {new Date(selectedJob.completed_at).toLocaleString()}</Typography>
              )}
              {selectedJob.error_message && (
                <Typography variant="body2" color="error" paragraph><strong>Error Message:</strong> {selectedJob.error_message}</Typography>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setSelectedJob(null)}>Close</Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};
