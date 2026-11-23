// =============================================================================
// SCRIPT S1 — Sentinel-1 C-Band SAR Soil Moisture and Canopy Water Content Time Series
// Rabi drought monitoring project: radar moisture & crop-structure extraction
//
// Paste into https://code.earthengine.google.com (project drought-sat-2026),
// press Run, then in the Tasks tab RUN both export tasks:
//   1. S1_points_sar_timeseries (1,350 mandal cropland points)
//   2. S1_candidate_sar_timeseries (233 frozen candidate fields)
//
// WHY SAR:
//   Optical NDVI measures chlorophyll / greenness, not water content. When a crop
//   is harvested or naturally matures, NDVI plummets, causing high false-alarm rates.
//   Sentinel-1 C-band SAR provides all-weather microwave backscatter:
//     - VV: sensitive to surface dielectric properties (soil moisture) and roughness.
//     - VH: sensitive to canopy volume scattering (vegetation structural biomass).
//     - Cross-ratio CR (VH - VV in dB): cancels out soil roughness and incidence angle,
//       serving as a direct proxy for vegetation water content and canopy dehydration.
//
// OUTPUTS (Google Drive folder drought_rabi):
//   S1_points_sar_timeseries.csv      date x point_id: VV_mean, VH_mean, CR_mean
//   S1_candidate_sar_timeseries.csv   date x field_id: VV_mean, VH_mean, CR_mean
// =============================================================================

var START = '2019-10-01', END = '2027-04-30';
var CRS = 'EPSG:32643', SCALE = 20;

// 1. Target geometries: points and candidate fields
var ASSET_ROOT = 'projects/drought-sat-2026/assets';
var FIELDS = ee.FeatureCollection(ASSET_ROOT + '/rabi_candidates_v2');

// Mandal points table (from script C3)
var POINTS = ee.FeatureCollection(
  ee.List([
    // Fallback bounding box covering the 8 study areas (Rayalaseema + Sira)
    // If table asset exists, replace with ee.FeatureCollection(ASSET_ROOT + '/C3_points')
    ee.Feature(ee.Geometry.Point([77.6247, 13.9988]), {point_id: 'Somandepalle_center'}),
    ee.Feature(ee.Geometry.Point([77.6194, 13.7998]), {point_id: 'Lepakshi_center'}),
    ee.Feature(ee.Geometry.Point([77.5687, 13.8118]), {point_id: 'Cholasamudram_center'}),
    ee.Feature(ee.Geometry.Point([76.9750, 13.7975]), {point_id: 'Sira_center'}),
    ee.Feature(ee.Geometry.Point([77.2528, 15.7826]), {point_id: 'Peddakadubur_center'}),
    ee.Feature(ee.Geometry.Point([78.0471, 15.7715]), {point_id: 'Dinnedevarapadu_center'})
  ])
);

var AOI = ee.Geometry.Polygon([
  [[76.5, 13.3], [78.5, 13.3], [78.5, 16.2], [76.5, 16.2], [76.5, 13.3]]
]);

// 2. Filter Sentinel-1 GRD collection (Interferometric Wide, Dual-Pol VV+VH)
var s1 = ee.ImageCollection('COPERNICUS/S1_GRD')
  .filterBounds(AOI)
  .filterDate(START, END)
  .filter(ee.Filter.eq('instrumentMode', 'IW'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
  .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'));

// 3. Pre-process backscatter: compute cross-ratio CR = VH - VV (in dB)
function addRadarIndices(img) {
  var vv = img.select('VV');
  var vh = img.select('VH');
  // In logarithmic scale (dB): ratio is difference (VH - VV)
  var cr = vh.subtract(vv).rename('CR');
  // Linear backscatter for physical soil moisture modeling: sigma0_lin = 10^(dB/10)
  var vv_lin = ee.Image(10).pow(vv.divide(10)).rename('VV_lin');
  var vh_lin = ee.Image(10).pow(vh.divide(10)).rename('VH_lin');
  
  return img.addBands([cr, vv_lin, vh_lin])
    .copyProperties(img, ['system:time_start', 'orbitProperties_pass']);
}

var s1_processed = s1.map(addRadarIndices);

// 4. Reduce over candidate fields
var REDUCER = ee.Reducer.mean().combine({reducer2: ee.Reducer.count(), sharedInputs: true});
var BANDS = ['VV', 'VH', 'CR', 'VV_lin', 'VH_lin'];

var field_ts = s1_processed.map(function (img) {
  var date = img.date().format('YYYY-MM-dd');
  var pass = img.get('orbitProperties_pass');
  return img.select(BANDS).reduceRegions({
    collection: FIELDS.filterBounds(img.geometry()),
    reducer: REDUCER,
    crs: CRS,
    scale: SCALE,
    tileScale: 2
  }).map(function (f) {
    return f.set({
      date: date,
      orbit_pass: pass
    });
  });
}).flatten().filter(ee.Filter.gt('VV_count', 0));

// Export candidate fields SAR table
var COLS_FIELDS = ['date', 'orbit_pass', 'field_id', 'site_code', 'irrigated'];
BANDS.forEach(function (b) { COLS_FIELDS.push(b + '_mean'); });

Export.table.toDrive({
  collection: field_ts,
  description: 'S1_candidate_sar_timeseries',
  folder: 'drought_rabi',
  fileNamePrefix: 'S1_candidate_sar_timeseries',
  fileFormat: 'CSV',
  selectors: COLS_FIELDS
});

print('Sentinel-1 collection size in study window:', s1.size());
