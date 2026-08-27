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
  MenuItem,
  TextField,
  Pagination,
  Grid,
  Card,
} from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export const LogsPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [level, setLevel] = useState('');

  const { data } = useQuery({
    queryKey: ['logs', page, level],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '50',
        ...(level && { level }),
      });
      return (await apiClient.get(`/logs?${params}`)).data;
    },
  });

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        System Execution Logs
      </Typography>

      <Card sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={4}>
            <TextField
              select
              fullWidth
              size="small"
              label="Filter Log Level"
              value={level}
              onChange={(e) => { setLevel(e.target.value); setPage(1); }}
            >
              <MenuItem value="">All Levels</MenuItem>
              <MenuItem value="INFO">INFO</MenuItem>
              <MenuItem value="WARNING">WARNING</MenuItem>
              <MenuItem value="ERROR">ERROR</MenuItem>
              <MenuItem value="CRITICAL">CRITICAL</MenuItem>
            </TextField>
          </Grid>
        </Grid>
      </Card>

      <TableContainer component={Paper} sx={{ borderRadius: 3, border: 1, borderColor: 'divider' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Level</TableCell>
              <TableCell>Message</TableCell>
              <TableCell>Page</TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Timestamp</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(data?.items || []).map((log: any) => (
              <TableRow key={log.id} hover>
                <TableCell>#{log.id}</TableCell>
                <TableCell>
                  <Chip
                    label={log.level}
                    size="small"
                    color={
                      log.level === 'ERROR' || log.level === 'CRITICAL'
                        ? 'error'
                        : log.level === 'WARNING'
                        ? 'warning'
                        : 'info'
                    }
                  />
                </TableCell>
                <TableCell sx={{ fontFamily: 'monospace' }}>{log.message}</TableCell>
                <TableCell>{log.page || '-'}</TableCell>
                <TableCell>{log.company || '-'}</TableCell>
                <TableCell>{new Date(log.created_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination count={Math.ceil((data?.total || 0) / 50)} page={page} onChange={(_, p) => setPage(p)} color="primary" />
      </Box>
    </Box>
  );
};
