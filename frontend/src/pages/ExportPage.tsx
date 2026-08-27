import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
} from '@mui/material';
import { Description as ExcelIcon, TableChart as CsvIcon, Download as DownloadIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export const ExportPage: React.FC = () => {
  const [error, setError] = React.useState<string | null>(null);
  const [downloading, setDownloading] = React.useState<'excel' | 'csv' | null>(null);
  const { data: history } = useQuery({
    queryKey: ['export-history'],
    queryFn: async () => (await apiClient.get('/export/history')).data,
  });

  const handleDownload = async (type: 'excel' | 'csv') => {
    setError(null);
    setDownloading(type);
    try {
      const response = await apiClient.get(`/export/${type}`, {
        responseType: 'blob',
      });
      const mimeType = type === 'excel'
        ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        : 'text/csv';
      const blob = new Blob([response.data], { type: mimeType });
      const link = document.createElement('a');
      link.href = window.URL.createObjectURL(blob);
      const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      link.download = `StartupTN_Companies_${dateStr}.${type === 'excel' ? 'xlsx' : 'csv'}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error('Export download failed', error);
      setError((error as any)?.response?.data?.detail || `Could not generate the ${type.toUpperCase()} export.`);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        Data Export Center
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>{error}</Alert>}

      {/* Instant Export Action Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6}>
          <Card sx={{ p: 2 }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <ExcelIcon color="success" sx={{ fontSize: 48 }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Export to Excel (.xlsx)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Includes styled headers, auto-width columns, and all 19 company fields.
                  </Typography>
                </Box>
              </Box>

              <Button
                variant="contained"
                color="success"
                size="large"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('excel')}
                disabled={downloading !== null}
              >
                Download Excel File
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6}>
          <Card sx={{ p: 2 }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <CsvIcon color="primary" sx={{ fontSize: 48 }} />
                <Box>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Export to CSV (.csv)
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    UTF-8 encoded standard CSV suitable for database imports and data tools.
                  </Typography>
                </Box>
              </Box>

              <Button
                variant="contained"
                color="primary"
                size="large"
                startIcon={<DownloadIcon />}
                onClick={() => handleDownload('csv')}
                disabled={downloading !== null}
              >
                Download CSV File
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Export History Table */}
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
        Generated Export History
      </Typography>
      <TableContainer component={Paper} sx={{ borderRadius: 3, border: 1, borderColor: 'divider' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>Filename</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Total Records</TableCell>
              <TableCell>Size (KB)</TableCell>
              <TableCell>Generated At</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {(history || []).map((item: any) => (
              <TableRow key={item.id} hover>
                <TableCell>#{item.id}</TableCell>
                <TableCell>{item.filename}</TableCell>
                <TableCell>
                  <Chip
                    label={item.file_type.toUpperCase()}
                    color={item.file_type === 'excel' ? 'success' : 'primary'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{item.total_records}</TableCell>
                <TableCell>{item.file_size ? (item.file_size / 1024).toFixed(1) : '-'}</TableCell>
                <TableCell>{new Date(item.created_at).toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
};
