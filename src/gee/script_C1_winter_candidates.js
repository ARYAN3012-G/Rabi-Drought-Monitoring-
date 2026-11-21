// =============================================================================
// SCRIPT C1 — Historically winter-active CANDIDATE fields (rabi project, pilot)
// Paste into https://code.earthengine.google.com and press Run.
// =============================================================================
// Selection uses ONLY the four complete reference seasons 2019-20, 2020-21, 2021-22, 2022-23
// (season y = 1 Oct y - 30 Apr y+1). Later seasons never influence which fields are chosen.
//
// Per pixel, inside the farmland mask of the satellite module (script A, cropland_mask_v2):
//  1. OBSERVED season: >= MIN_OBS clear Sentinel-2 images between 1 Jan and 31 Mar.
//  2. WINTER-ACTIVE season: observed, and
//       median NDVI over 1 Jan - 31 Mar > WINTER_GREEN   (green for at least half of Jan-Mar)
//       and NDVI 90th - 10th percentile over Oct-Apr > AMPLITUDE (it rises and/or falls:
//       removes vegetation that is green all year).
//  3. HISTORICALLY WINTER-ACTIVE: observed in >= MIN_OBS_SEASONS of the 4 seasons and winter-active
//     in >= MIN_ACTIVE_SEASONS of them.
// These are CANDIDATES (winter vegetation activity), not verified rabi crops: crop type and
// sowing date are not known. Late kharif crops still green in January can pass.
//  4. Field-sized segments (SNIC) on the candidate pixels, 0.3-10 ha, >= 50 % candidate pixels.
//  5. Rainfed / irrigated: the frozen summer rule of the satellite module (mask band 'irrigated',
//     green in Mar-May in >= 2 of 2019-2023), kept SEPARATE.
//  6. Random sample per site (fixed seed): up to N_PER_CLASS rainfed + N_PER_CLASS irrigated.
//     If a site has fewer, all are kept and the count is reported (it does NOT mean no rabi crops).
// Every candidate carries its selection reasons (per-season activity, observations, Jan-Mar NDVI).
//
// Outputs (Tasks tab -> RUN each):
//  C1_stats                      CSV      hectares per step, per site
//  C1_candidates_<site>  (x8)    GeoJSON  all candidate segments with reasons (sampled = 1/0)
//  C1_sampled_asset              Asset    the sampled candidates -> input of script C2
// =============================================================================

// ---- 0. SETTINGS -------------------------------------------------------------
var ASSET_ROOT = 'projects/drought-sat-2026/assets';        // your project (assets are written here)
var MASK_ROOT  = 'projects/serverchat-489517/assets';       // cropland_mask_v2 from script A
var SEASONS = [2019, 2020, 2021, 2022];                     // reference seasons (start year)
var MIN_OBS = 4;                 // clear images needed in Jan-Mar for a season to count as observed
var WINTER_GREEN = 0.35;         // Jan-Mar median NDVI above this = green in winter
var AMPLITUDE = 0.15;            // Oct-Apr NDVI p90 - p10 above this = not evergreen
var MIN_OBS_SEASONS = 3;         // observed in >= 3 of 4 seasons
var MIN_ACTIVE_SEASONS = 2;      // winter-active in >= 2 of 4 seasons
var CLOUD_CS = 0.60;
var SNIC_SIZE = 8;
var MIN_PIX = 30, MAX_PIX = 1000;
var N_PER_CLASS = 20, SEED = 42;
var CRS = 'EPSG:32643', SCALE = 10;

var SITES = [
  {code: 'Som',  name: 'Somandepalle',            lat: 13.9988, lon: 77.6247},
  {code: 'Lep',  name: 'Lepakshi',                lat: 13.7998, lon: 77.6194},
  {code: 'Cho',  name: 'Cholasamudram',           lat: 13.8118, lon: 77.5687},
  {code: 'Sira', name: 'Sira',                    lat: 13.7975, lon: 76.9750},
  {code: 'Ped',  name: 'Peddakadubur',            lat: 15.7826, lon: 77.2528},
  {code: 'Din',  name: 'Kurnool_Dinnedevarapadu', lat: 15.7715, lon: 78.0471},
  {code: 'Bal',  name: 'Kurnool_Balaji_Villas',   lat: 15.7834, lon: 78.0561},
  {code: 'Pul',  name: 'Kurnool_Pullaiah',        lat: 15.7982, lon: 78.0806}
];
var circles = SITES.map(function (s) {
  return ee.Feature(ee.Geometry.Point([s.lon, s.lat]).buffer(3000), {site: s.name, site_code: s.code});
});
var AOI = ee.FeatureCollection(circles).geometry();

// Farmland mask of the satellite module: band 'site' (0-7, same order as SITES), band 'irrigated'
var MASK = ee.Image(MASK_ROOT + '/cropland_mask_v2');
var farmland = MASK.select('site').mask().gt(0).unmask(0);

// ---- Sentinel-2 NDVI with Cloud Score+ and SCL masking (as script B) -----------------
var CSP = ee.ImageCollection('GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED');
function ndvi(start, end) {
  return ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
    .filterBounds(AOI).filterDate(start, end)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 90))
    .linkCollection(CSP, ['cs_cdf'])
    .map(function (img) {
      var scl = img.select('SCL');
      var clear = img.select('cs_cdf').gte(CLOUD_CS)
        .and(scl.neq(1)).and(scl.neq(3)).and(scl.neq(8)).and(scl.neq(9))
        .and(scl.neq(10)).and(scl.neq(11));
      return img.normalizedDifference(['B8', 'B4']).rename('NDVI').updateMask(clear);
    });
}

// ---- 1-3. Per season: observed, winter-active; then counts over the 4 seasons -----------
var perSeason = SEASONS.map(function (y) {
  var jm = ndvi((y + 1) + '-01-01', (y + 1) + '-04-01');
  var oa = ndvi(y + '-10-01', (y + 1) + '-05-01');
  var nObs = jm.count().rename('obs_' + y).unmask(0);
  var jmMed = jm.median().rename('jm_ndvi_' + y);
  var p = oa.reduce(ee.Reducer.percentile([10, 90]));
  var amp = p.select('NDVI_p90').subtract(p.select('NDVI_p10'));
  var observed = nObs.gte(MIN_OBS);
  var active = observed.and(jmMed.gt(WINTER_GREEN)).and(amp.gt(AMPLITUDE)).unmask(0)
                 .rename('active_' + y);
  return {obs: observed.rename('observed_' + y), active: active, jm: jmMed.unmask(-1), n: nObs};
});
var nObserved = ee.Image(perSeason.map(function (s) { return s.obs; })).reduce(ee.Reducer.sum());
var nActive = ee.Image(perSeason.map(function (s) { return s.active; })).reduce(ee.Reducer.sum());
var candidate = farmland.and(nObserved.gte(MIN_OBS_SEASONS)).and(nActive.gte(MIN_ACTIVE_SEASONS));

// reasons image (averaged per segment later)
var reasons = ee.Image.cat(
  perSeason.map(function (s) { return s.active.toFloat(); })
    .concat(perSeason.map(function (s) { return s.n.toFloat(); }))
    .concat(perSeason.map(function (s) { return s.jm.toFloat(); }))
).addBands(nActive.rename('n_active_seasons').toFloat())
 .addBands(nObserved.rename('n_observed_seasons').toFloat())
 .addBands(MASK.select('irrigated').unmask(0).rename('irrig_frac').toFloat())
 .addBands(candidate.rename('candidate_frac').toFloat());

// ---- 4. Segments on candidate pixels (features: Jan-Mar medians of the 4 seasons) --------
var feat = ee.Image.cat(perSeason.map(function (s, k) { return s.jm.rename('f' + k); }))
             .updateMask(candidate);
var snic = ee.Algorithms.Image.Segmentation.SNIC({
  image: feat, size: SNIC_SIZE, compactness: 1, connectivity: 8,
  neighborhoodSize: 4 * SNIC_SIZE,
  seeds: ee.Algorithms.Image.Segmentation.seedGrid(SNIC_SIZE)
}).select('clusters').reproject({crs: CRS, scale: SCALE});

function siteCandidates(s, i) {
  var inSite = MASK.select('site').eq(i).unmask(0);
  var vec = snic.addBands(candidate.toFloat().rename('c')).updateMask(candidate.and(inSite))
    .reduceToVectors({
      geometry: circles[i].geometry(), crs: CRS, scale: SCALE, geometryType: 'polygon',
      eightConnected: true, labelProperty: 'label', reducer: ee.Reducer.count(), maxPixels: 1e10
    }).filter(ee.Filter.rangeContains('count', MIN_PIX, MAX_PIX));
  // selection reasons = mean of each reasons band over the segment
  vec = reasons.reduceRegions({collection: vec, reducer: ee.Reducer.mean(), crs: CRS, scale: SCALE,
                               tileScale: 4});
  vec = vec.map(function (f) {
    var n = ee.Number(f.get('count'));
    var id = ee.String('W' + s.code + '_').cat(ee.Number(f.get('label')).format('%d'))
               .cat('_').cat(n.format('%d'));
    return f.set({field_id: id, site: s.name, site_code: s.code, pixels: n, area_ha: n.divide(100),
                  irrigated: ee.Number(f.get('irrig_frac')).gte(0.5)});
  }).filter(ee.Filter.gte('candidate_frac', 0.5));
  var rain = vec.filter(ee.Filter.eq('irrigated', 0)).randomColumn('r', SEED).sort('r').limit(N_PER_CLASS);
  var irr  = vec.filter(ee.Filter.eq('irrigated', 1)).randomColumn('r', SEED).sort('r').limit(N_PER_CLASS);
  var ids = rain.merge(irr).aggregate_array('field_id');
  return vec.map(function (f) {
    return f.set('sampled', ee.Algorithms.If(ids.contains(f.get('field_id')), 1, 0));
  });
}

// ---- Per-site statistics -------------------------------------------------------------
var stats = ee.FeatureCollection(SITES.map(function (s, i) {
  var inSite = MASK.select('site').eq(i).unmask(0);
  var irr = MASK.select('irrigated').unmask(0);
  var img = ee.Image.cat([
    inSite, inSite.and(nObserved.gte(MIN_OBS_SEASONS)), inSite.and(candidate),
    inSite.and(candidate).and(irr.not()), inSite.and(candidate).and(irr)
  ]).rename(['farmland_ha', 'well_observed_ha', 'candidate_ha', 'candidate_rainfed_ha',
             'candidate_irrigated_ha']).multiply(ee.Image.pixelArea().divide(1e4));
  var sums = img.reduceRegion({reducer: ee.Reducer.sum(), geometry: circles[i].geometry(),
                               crs: CRS, scale: SCALE, maxPixels: 1e10, tileScale: 16});
  return ee.Feature(null, sums).set({site: s.name, site_code: s.code});
}));

// ---- Exports (one per site keeps memory low) ---------------------------------------------
Export.table.toDrive({collection: stats, description: 'C1_stats', folder: 'drought_rabi',
  fileNamePrefix: 'C1_stats', fileFormat: 'CSV'});
var sampledAll = [];
SITES.forEach(function (s, i) {
  var c = siteCandidates(s, i);
  Export.table.toDrive({collection: c, description: 'C1_candidates_' + s.code, folder: 'drought_rabi',
    fileNamePrefix: 'C1_candidates_' + s.code, fileFormat: 'GeoJSON'});
  sampledAll.push(c.filter(ee.Filter.eq('sampled', 1)));
});
Export.table.toAsset({collection: ee.FeatureCollection(sampledAll).flatten(),
  description: 'C1_sampled_asset', assetId: ASSET_ROOT + '/rabi_candidates_v1'});

// ---- Map for visual checking -----------------------------------------------------------
Map.addLayer(ndvi('2023-01-01', '2023-04-01').median().clip(AOI),
             {min: 0, max: 0.8, palette: ['brown', 'yellow', 'green']}, 'Jan-Mar 2023 NDVI', false);
Map.addLayer(farmland.selfMask(), {palette: ['ffff00'], opacity: 0.4}, 'Farmland (script A)');
Map.addLayer(candidate.and(MASK.select('irrigated').unmask(0).not()).selfMask(),
             {palette: ['ff8800']}, 'Winter-active candidates, rainfed');
Map.addLayer(candidate.and(MASK.select('irrigated').unmask(0)).selfMask(),
             {palette: ['00bfff']}, 'Winter-active candidates, irrigated');
Map.addLayer(ee.Image().byte().paint(ee.FeatureCollection(circles), 0, 2), {palette: ['ff0000']}, '3 km circles');
var picker = ui.Select({items: SITES.map(function (s) { return s.name; }), placeholder: 'Go to site',
  onChange: function (name) {
    var s = SITES.filter(function (x) { return x.name === name; })[0];
    Map.setCenter(s.lon, s.lat, 14);
  }});
Map.add(ui.Panel([ui.Label('Script C1: winter-active candidates', {fontWeight: 'bold'}), picker,
                  ui.Label('Orange = rainfed candidates'), ui.Label('Blue = irrigated candidates')],
                 null, {position: 'top-left', width: '240px'}));
Map.setOptions('SATELLITE');
Map.setCenter(SITES[5].lon, SITES[5].lat, 13);
print('Next: Tasks tab -> RUN all 10 exports (C1_stats, 8 x C1_candidates_<site>, C1_sampled_asset).');
