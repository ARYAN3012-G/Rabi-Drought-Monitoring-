// =====================================================================================
// Script D2 - MODIS rabi greenness 2000-01 .. 2025-26 for the combined rabi module.
// Supersedes D1 (never run). Earth Engine project: drought-sat-2026.
//
// Units (11): 3 districts (FAO GAUL 2015 level 2: Kurnool, Anantapur, Tumkur)
//             + 8 study sites (cropland within 3 km of the site centre, data/sites.csv).
// Cropland: ESA WorldCover v100 (2020) class 40 (fixed mask, all years).
// NDVI/EVI: MODIS Terra MOD13Q1 v061, 250 m, 16-day; pixels with SummaryQA <= 1 only.
// Months: Sep - Apr (rabi + sowing). No reference / VCI computed here: done in Python
// (src/combined/modis.py) so that the reference seasons are fixed in code, not here.
//
// Export: drought2_D2_modis_rabi.csv  (Drive folder drought_rabi) -> copy to data/modis/
//   unit, unit_type, date, ndvi_mean, evi_mean, ndvi_count, crop_pixels
// =====================================================================================
var SITES = [
  ['Som', 13.9988, 77.6247], ['Lep', 13.7998, 77.6194], ['Cho', 13.8118, 77.5687],
  ['Sira', 13.7975, 76.9750], ['Ped', 15.7826, 77.2528], ['Din', 15.7715, 78.0471],
  ['Bal', 15.7834, 78.0561], ['Pul', 15.7982, 78.0806]
];
var siteFc = ee.FeatureCollection(SITES.map(function (s) {
  return ee.Feature(ee.Geometry.Point([s[2], s[1]]).buffer(3000), {unit: s[0], unit_type: 'site'});
}));
var distFc = ee.FeatureCollection('FAO/GAUL/2015/level2')
  .filter(ee.Filter.inList('ADM2_NAME', ['Kurnool', 'Anantapur', 'Tumkur']))
  .map(function (f) { return ee.Feature(f.geometry(), {unit: f.get('ADM2_NAME'), unit_type: 'district'}); });
var UNITS = distFc.merge(siteFc);
print('Units (must be 11: 3 districts + 8 sites)', UNITS.size());

var crop = ee.ImageCollection('ESA/WorldCover/v100').first().eq(40);
var cropPix = crop.selfMask().rename('crop').reduceRegions({collection: UNITS, reducer: ee.Reducer.count(),
                                                            scale: 250, tileScale: 4});
print('Cropland 250 m pixels per unit (check none is 0)', cropPix.aggregate_array('count'));
var cropDict = ee.Dictionary.fromLists(cropPix.aggregate_array('unit'), cropPix.aggregate_array('count'));

var mod = ee.ImageCollection('MODIS/061/MOD13Q1')
  .filterDate('2000-02-18', '2026-05-01')
  .filter(ee.Filter.calendarRange(9, 4, 'month'))   // Sep..Apr (wraps over the year end)
  .map(function (im) {
    var ok = im.select('SummaryQA').lte(1);
    return im.select(['NDVI', 'EVI']).multiply(0.0001).updateMask(ok).updateMask(crop)
      .copyProperties(im, ['system:time_start']);
  });
print('MODIS composites used', mod.size());

var rows = mod.map(function (im) {
  var date = ee.Date(im.get('system:time_start')).format('YYYY-MM-dd');
  return im.reduceRegions({collection: UNITS,
                           reducer: ee.Reducer.mean().combine(ee.Reducer.count(), '', true),
                           scale: 250, tileScale: 4})
    .map(function (f) {
      return ee.Feature(null, {unit: f.get('unit'), unit_type: f.get('unit_type'), date: date,
                               ndvi_mean: f.get('NDVI_mean'), evi_mean: f.get('EVI_mean'),
                               ndvi_count: f.get('NDVI_count'), crop_pixels: cropDict.get(f.get('unit'))});
    });
}).flatten();

Export.table.toDrive({collection: rows, description: 'drought2_D2_modis_rabi', folder: 'drought_rabi',
  fileNamePrefix: 'drought2_D2_modis_rabi', fileFormat: 'CSV',
  selectors: ['unit', 'unit_type', 'date', 'ndvi_mean', 'evi_mean', 'ndvi_count', 'crop_pixels']});
