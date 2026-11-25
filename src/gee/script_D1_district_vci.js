// =====================================================================================
// Script D1 - district rabi vegetation condition (VCI) 2000-01 .. 2022-23 for drought v2.
// NOT RUN YET (requires the user's Earth Engine account). Output used only for the
// vegetation-condition indicator alongside soil-moisture deficit duration.
//
// Districts (pre-2022, FAO GAUL 2015 level 2): Kurnool, Anantapur (AP), Tumkur (KA).
// Cropland mask: ESA WorldCover 2020 class 40 (fixed). NDVI: MODIS MOD13Q1 v061 (250 m, 16-day),
// quality: SummaryQA <= 1. VCI per pixel and 16-day composite = (NDVI - min) / (max - min) with
// min/max from the reference seasons 2000-01 .. 2009-10 only (same composite day-of-year).
// Export: one row per district x composite date (Oct - Apr):
//   district, date, ndvi_mean, vci_mean, valid_fraction
// File: drought2_D1_district_vci.csv (Drive folder drought_rabi). Copy it to data/drought2/.
// =====================================================================================
var DIST = ee.FeatureCollection('FAO/GAUL/2015/level2')
  .filter(ee.Filter.inList('ADM2_NAME', ['Kurnool', 'Anantapur', 'Tumkur']));
var crop = ee.ImageCollection('ESA/WorldCover/v100').first().eq(40);
var mod = ee.ImageCollection('MODIS/061/MOD13Q1').filterDate('2000-02-18', '2023-05-01')
  .map(function (im) {
    var ok = im.select('SummaryQA').lte(1);
    return im.select('NDVI').multiply(0.0001).updateMask(ok).updateMask(crop)
      .set('doy', ee.Date(im.get('system:time_start')).getRelative('day', 'year'))
      .copyProperties(im, ['system:time_start']);
  });
var ref = mod.filterDate('2000-07-01', '2010-06-30');

var withVci = mod.filter(ee.Filter.calendarRange(10, 4, 'month')).map(function (im) {
  var same = ref.filter(ee.Filter.eq('doy', im.get('doy')));
  var mn = same.min(), mx = same.max();
  var vci = im.subtract(mn).divide(mx.subtract(mn)).clamp(0, 1).rename('VCI');
  return im.addBands(vci).copyProperties(im, ['system:time_start']);
});

var rows = withVci.map(function (im) {
  var date = ee.Date(im.get('system:time_start')).format('YYYY-MM-dd');
  return im.reduceRegions({collection: DIST, reducer: ee.Reducer.mean().combine(ee.Reducer.count(), '', true),
                           scale: 250, tileScale: 4})
    .map(function (f) {
      return ee.Feature(null, {district: f.get('ADM2_NAME'), date: date, ndvi_mean: f.get('NDVI_mean'),
                               vci_mean: f.get('VCI_mean'), ndvi_count: f.get('NDVI_count')});
    });
}).flatten();

// valid fraction = observed cropland pixels / all cropland pixels of the district
var cropCount = crop.selfMask().reduceRegions({collection: DIST, reducer: ee.Reducer.count(), scale: 250});
print('Cropland pixels per district', cropCount);
Export.table.toDrive({collection: rows, description: 'drought2_D1_district_vci', folder: 'drought_rabi',
  fileNamePrefix: 'drought2_D1_district_vci', fileFormat: 'CSV',
  selectors: ['district', 'date', 'ndvi_mean', 'vci_mean', 'ndvi_count']});
