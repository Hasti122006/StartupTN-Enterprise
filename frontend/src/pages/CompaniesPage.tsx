import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  TextField,
  MenuItem,
  Pagination,
  IconButton,
  Drawer,
  Chip,
  Divider,
  Grid,
  Link,
  Avatar,
  Skeleton,
  CircularProgress,
  Alert,
  Button,
} from '@mui/material';
import {
  Search as SearchIcon,
  Visibility as ViewIcon,
  Language as WebIcon,
  LinkedIn as LinkedInIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  LocationOn as LocationIcon,
  Close as CloseIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../api/client';

export const CompaniesPage: React.FC = () => {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [sector, setSector] = useState('');
  const [stage, setStage] = useState('');
  const [selectedCompanyId, setSelectedCompanyId] = useState<number | null>(null);

  // Queries
  const { data, isLoading } = useQuery({
    queryKey: ['companies', page, search, sector, stage],
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        page_size: '5',
        ...(search && { search }),
        ...(sector && { sector }),
        ...(stage && { current_stage: stage }),
      });
      return (await apiClient.get(`/companies/?${params}`)).data;
    },
    refetchInterval: 3000,
  });

  const { data: sectorOptions } = useQuery({
    queryKey: ['filter-sectors'],
    queryFn: async () => (await apiClient.get('/companies/filters/sectors')).data,
  });

  const { data: stageOptions } = useQuery({
    queryKey: ['filter-stages'],
    queryFn: async () => (await apiClient.get('/companies/filters/stages')).data,
  });

  // Query for complete company details when an action button is clicked
  const {
    data: detailData,
    isLoading: isDetailLoading,
    isError: isDetailError,
  } = useQuery({
    queryKey: ['company-detail', selectedCompanyId],
    queryFn: async () => {
      if (!selectedCompanyId) return null;
      return (await apiClient.get(`/companies/${selectedCompanyId}/`)).data;
    },
    enabled: !!selectedCompanyId,
  });

  return (
    <Box>
      <Typography variant="h4" sx={{ mb: 3, fontWeight: 700 }}>
        StartupTN Companies Directory
      </Typography>

      {/* Search & Filter Bar */}
      <Card sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={5}>
            <TextField
              fullWidth
              size="small"
              placeholder="Search by company name, founders, location..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              InputProps={{
                startAdornment: <SearchIcon color="action" sx={{ mr: 1 }} />,
              }}
            />
          </Grid>

          <Grid item xs={6} sm={3.5}>
            <TextField
              select
              fullWidth
              size="small"
              label="Filter by Sector"
              value={sector}
              onChange={(e) => {
                setSector(e.target.value);
                setPage(1);
              }}
            >
              <MenuItem value="">All Sectors</MenuItem>
              {(sectorOptions || []).map((sec: string) => (
                <MenuItem key={sec} value={sec}>
                  {sec}
                </MenuItem>
              ))}
            </TextField>
          </Grid>

          <Grid item xs={6} sm={3.5}>
            <TextField
              select
              fullWidth
              size="small"
              label="Filter by Stage"
              value={stage}
              onChange={(e) => {
                setStage(e.target.value);
                setPage(1);
              }}
            >
              <MenuItem value="">All Stages</MenuItem>
              {(stageOptions || []).map((stg: string) => (
                <MenuItem key={stg} value={stg}>
                  {stg}
                </MenuItem>
              ))}
            </TextField>
          </Grid>
        </Grid>
      </Card>

      {/* Companies Table */}
      <TableContainer component={Paper} sx={{ borderRadius: 3, border: 1, borderColor: 'divider' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Company</TableCell>
              <TableCell>Founders</TableCell>
              <TableCell>Sector</TableCell>
              <TableCell>Stage</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Scraped At</TableCell>
              <TableCell align="right">Action</TableCell>
            </TableRow>
          </TableHead>

          <TableBody>
            {isLoading
              ? Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={i}>
                    <TableCell><Skeleton width={120} /></TableCell>
                    <TableCell><Skeleton width={100} /></TableCell>
                    <TableCell><Skeleton width={80} /></TableCell>
                    <TableCell><Skeleton width={80} /></TableCell>
                    <TableCell><Skeleton width={90} /></TableCell>
                    <TableCell><Skeleton width={100} /></TableCell>
                    <TableCell align="right"><Skeleton width={30} /></TableCell>
                  </TableRow>
                ))
              : (data?.items || []).map((c: any) => (
                  <TableRow key={c.id} hover>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Avatar src={c.logo_url || ''} sx={{ width: 36, height: 36 }}>
                          {c.company_name ? c.company_name.charAt(0) : 'C'}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                            {c.company_name}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {c.startup_type || 'Startup'}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>{c.founders || '-'}</TableCell>
                    <TableCell>
                      {c.sector ? <Chip label={c.sector} size="small" variant="outlined" /> : '-'}
                    </TableCell>
                    <TableCell>{c.current_stage || '-'}</TableCell>
                    <TableCell>{c.location || '-'}</TableCell>
                    <TableCell>
                      {c.scraped_at ? new Date(c.scraped_at).toLocaleDateString() : '-'}
                    </TableCell>
                    <TableCell align="right">
                      <IconButton color="primary" onClick={() => setSelectedCompanyId(c.id)}>
                        <ViewIcon />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination Controls */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination
          count={data?.total_pages || 1}
          page={page}
          onChange={(_, p) => setPage(p)}
          color="primary"
        />
      </Box>

      {/* Detail Slide-out Drawer */}
      <Drawer
        anchor="right"
        open={Boolean(selectedCompanyId)}
        onClose={() => setSelectedCompanyId(null)}
        PaperProps={{
          sx: {
            width: { xs: '100%', sm: 520 },
            p: 3,
            boxSizing: 'border-box',
            top: { xs: 56, sm: 64 },
            height: { xs: 'calc(100% - 56px)', sm: 'calc(100% - 64px)' },
            overflowY: 'auto',
          },
        }}
      >
        {/* Header with Close Button */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary">
            Company Record Details
          </Typography>
          <IconButton size="small" onClick={() => setSelectedCompanyId(null)}>
            <CloseIcon fontSize="small" />
          </IconButton>
        </Box>

        {isDetailLoading && (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 8 }}>
            <CircularProgress size={40} />
            <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary', fontWeight: 500 }}>
              Loading company details...
            </Typography>
          </Box>
        )}

        {isDetailError && (
          <Alert severity="error" sx={{ my: 2 }}>
            Unable to load company details.
          </Alert>
        )}

        {!isDetailLoading && !isDetailError && detailData && (
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
              <Avatar src={detailData.logo_url} sx={{ width: 56, height: 56 }}>
                {detailData.company_name ? detailData.company_name.charAt(0) : 'C'}
              </Avatar>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 700 }}>
                  {detailData.company_name}
                </Typography>
                <Chip label={detailData.current_stage || 'N/A'} color="primary" size="small" />
              </Box>
            </Box>

            <Divider sx={{ mb: 3 }} />

            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">Founders</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>
                  {Array.isArray(detailData.founders) ? detailData.founders.join(', ') : (detailData.founders || 'N/A')}
                </Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">Sector</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{detailData.sector || 'N/A'}</Typography>
              </Grid>

              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">Team Size</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{detailData.team_size || 'N/A'}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">Member Since</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{detailData.member_since || 'N/A'}</Typography>
              </Grid>

              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">Smart Card #</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{detailData.smart_card_number || 'N/A'}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography variant="caption" color="text.secondary">Engagement Level</Typography>
                <Typography variant="body2" sx={{ fontWeight: 500 }}>{detailData.engagement_level || 'N/A'}</Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">Location</Typography>
                <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <LocationIcon fontSize="small" color="action" /> {detailData.location || 'N/A'}
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">Key Highlights</Typography>
                <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                  {Array.isArray(detailData.key_highlights) ? detailData.key_highlights.join('\n• ') : (detailData.key_highlights || 'N/A')}
                </Typography>
              </Grid>

              <Grid item xs={12}>
                <Typography variant="caption" color="text.secondary">About</Typography>
                <Typography variant="body2">{detailData.about || 'N/A'}</Typography>
              </Grid>

              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle1" sx={{ fontWeight: 600, color: '#38bdf8', mb: 2 }}>
                  Contact Details
                </Typography>

                {/* Email */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, fontWeight: 500 }}>
                    <EmailIcon fontSize="small" sx={{ color: '#38bdf8' }} /> Email: <strong>{detailData.email || 'Not available'}</strong>
                  </Typography>
                  {detailData.email && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, pl: 3.5 }}>
                      <Chip
                        label="Official Web ✓"
                        size="small"
                        sx={{
                          bgcolor: 'rgba(56, 189, 248, 0.15)',
                          color: '#38bdf8',
                          fontSize: '0.75rem',
                          height: 22,
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          fontWeight: 600,
                        }}
                      />
                      {detailData.website && (
                        <Link
                          href={detailData.website}
                          target="_blank"
                          underline="hover"
                          variant="caption"
                          sx={{ color: '#38bdf8', fontWeight: 500 }}
                        >
                          {detailData.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                        </Link>
                      )}
                    </Box>
                  )}
                </Box>

                {/* Phone */}
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, fontWeight: 500 }}>
                    <PhoneIcon fontSize="small" sx={{ color: '#38bdf8' }} /> Phone: <strong>{detailData.phone || 'Not available'}</strong>
                  </Typography>
                  {detailData.phone && (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5, pl: 3.5 }}>
                      <Chip
                        label="Official Web ✓"
                        size="small"
                        sx={{
                          bgcolor: 'rgba(56, 189, 248, 0.15)',
                          color: '#38bdf8',
                          fontSize: '0.75rem',
                          height: 22,
                          border: '1px solid rgba(56, 189, 248, 0.3)',
                          fontWeight: 600,
                        }}
                      />
                      {detailData.website && (
                        <Link
                          href={detailData.website}
                          target="_blank"
                          underline="hover"
                          variant="caption"
                          sx={{ color: '#38bdf8', fontWeight: 500 }}
                        >
                          {detailData.website.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                        </Link>
                      )}
                    </Box>
                  )}
                </Box>

                {/* LinkedIn */}
                <Box sx={{ mb: 2 }}>
                  {detailData.linkedin ? (
                    <Box>
                      <Link
                        href={detailData.linkedin}
                        target="_blank"
                        underline="hover"
                        sx={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: 1,
                          color: '#38bdf8',
                          fontWeight: 600,
                          fontSize: '0.95rem',
                        }}
                      >
                        <LinkedInIcon fontSize="small" /> Open LinkedIn
                      </Link>
                      <Box sx={{ mt: 0.5, pl: 3.5 }}>
                        <Chip
                          label="Official Web ✓"
                          size="small"
                          sx={{
                            bgcolor: 'rgba(56, 189, 248, 0.15)',
                            color: '#38bdf8',
                            fontSize: '0.75rem',
                            height: 22,
                            border: '1px solid rgba(56, 189, 248, 0.3)',
                            fontWeight: 600,
                          }}
                        />
                      </Box>
                    </Box>
                  ) : (
                    <Typography variant="body2" sx={{ display: 'flex', alignItems: 'center', gap: 1, color: 'text.secondary' }}>
                      <LinkedInIcon fontSize="small" /> LinkedIn: Not available
                    </Typography>
                  )}
                </Box>

                {/* Official Website */}
                <Box sx={{ mb: 2.5 }}>
                  {detailData.website ? (
                    <Link
                      href={detailData.website}
                      target="_blank"
                      underline="hover"
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1,
                        color: '#38bdf8',
                        fontWeight: 600,
                        fontSize: '0.95rem',
                      }}
                    >
                      <WebIcon fontSize="small" /> Official Website
                    </Link>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      Website: Not available
                    </Typography>
                  )}
                </Box>

                {/* StartupTN Profile URL */}
                <Box sx={{ mb: 1 }}>
                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 0.5 }}>
                    StartupTN Profile URL
                  </Typography>
                  <Link
                    href={detailData.profile_url || `https://startuptn.in/ecosystem-info?userid=${detailData.id}`}
                    target="_blank"
                    underline="hover"
                    variant="body2"
                    sx={{ color: '#38bdf8', wordBreak: 'break-all', fontWeight: 500 }}
                  >
                    {detailData.profile_url || `https://startuptn.in/ecosystem-info?userid=${detailData.id}`}
                  </Link>
                </Box>
              </Grid>
            </Grid>
          </Box>
        )}
      </Drawer>
    </Box>
  );
};
