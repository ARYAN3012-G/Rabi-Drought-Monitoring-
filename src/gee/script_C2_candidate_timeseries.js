// =============================================================================
// SCRIPT C2 — Sentinel-2 time series of the sampled winter-active candidates (rabi project)
// Needs the asset rabi_candidates_v1 written by script C1 (Assets tab: wait until it appears).
// Paste into https://code.earthengine.google.com, press Run, Tasks tab -> RUN C2_candidate_timeseries_<VERSION>.
// Re-run during the season (Dec 2026 - Mar 2027) to add new images: END is far in the future, so
// every run simply contains all images available on that day.
// =============================================================================
// Output (Google Drive folder drought_rabi):
//  C2_candidate_timeseries.csv  one row per candidate field per clear Sentinel-2 image:
//      mean reflectance (B2-B12), NDVI, NDMI, EVI, clear pixel count - same columns as script B of
//      the satellite module, so its cleaning code can be reused.
// =============================================================================

var ASSET_ROOT = 'projects/drought-sat-2026/assets';
var START = '2019-10-01', END = '2027-06-01';
var CLOUD_CS = 0.60;
var CRS = 'EPSG:32643', SCALE = 10;

var VERSION = 'v2';             // which C1 asset: 'v1' (first run) or 'v2' (rise rule)
var FIELDS = ee.FeatureCollection(ASSET_ROOT + '/rabi_candidates_' + VERSION);
var AOI = FIELDS.geometry().bounds();

var CSP = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
var REFL = ['B2', 'B3', 'B4', 'B5', 'B8', 'B11', 'B12'];
var S2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(AOI).filterDate(START, END)
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 90))
  .linkCollection(CSP, ['cs_cdf'])
  .map(function (img) {
    var scl = img.select('SCL');
    var clear = img.select('cs_cdf').gte(CLOUD_CS)
      .and(scl.neq(1)).and(scl.neq(3)).and(scl.neq(8)).and(scl.neq(9))
      .and(scl.neq(10)).and(scl.neq(11));
    var r = img.select(REFL).divide(10000);
    var ndvi = r.normalizedDifference(['B8', 'B4']).rename('NDVI');
    var ndmi = r.normalizedDifference(['B8', 'B11']).rename('NDMI');
    var evi = r.expression('2.5 * (N - R) / (N + 6 * R - 7.5 * B + 1)',
      {N: r.select('B8'), R: r.select('B4'), B: r.select('B2')}).rename('EVI');
    return r.addBands([ndvi, ndmi, evi]).updateMask(clear)
      .copyProperties(img, ['system:time_start', 'MGRS_TILE', 'CLOUDY_PIXEL_PERCENTAGE']);
  });

var BANDS = REFL.concat(['NDVI', 'NDMI', 'EVI']);
var red = ee.Reducer.mean().combine({reducer2: ee.Reducer.count(), sharedInputs: true});
var ts = S2.map(function (img) {
  var date = img.date().format('YYYY-MM-dd');
  return img.select(BANDS).reduceRegions({
    collection: FIELDS.filterBounds(img.geometry()), reducer: red, crs: CRS, scale: SCALE, tileScale: 2
  }).map(function (f) {
    return f.set({date: date, tile: img.get('MGRS_TILE'), scene_cloud_pct: img.get('CLOUDY_PIXEL_PERCENTAGE')});
  });
}).flatten().filter(ee.Filter.gt('NDVI_count', 0));

var COLS = ['date', 'tile', 'scene_cloud_pct', 'field_id', 'site', 'site_code', 'irrigated',
            'area_ha', 'pixels', 'NDVI_count'];
BANDS.forEach(function (b) { COLS.push(b + '_mean'); });
Export.table.toDrive({collection: ts, description: 'C2_candidate_timeseries_' + VERSION, folder: 'drought_rabi',
  fileNamePrefix: 'C2_candidate_timeseries_' + VERSION, fileFormat: 'CSV', selectors: COLS});

print('Sampled candidate fields:', FIELDS.size());
print('Per site and class:', FIELDS.aggregate_histogram('site_code'),
      FIELDS.aggregate_histogram('irrigated'));
Map.addLayer(FIELDS, {color: 'ff8800'}, 'Sampled winter-active candidates');
Map.centerObject(FIELDS, 9);
print('Next: Tasks tab -> RUN C2_candidate_timeseries_<VERSION>.');
