var setupCharts = function(playerid) {
    $.get('/api/playermatches/' + playerid, function(model_) {
        // scaled y-axis, see https://github.com/dc-js/dc.js/issues/667
        function nonzero_min(chart) {
            dc.override(chart, 'yAxisMin', function () {
                var min = d3.min(chart.data(), function (layer) {
                    return d3.min(layer.values, function (p) {
                        return p.y + p.y0;
                    });
                });
                return dc.utils.subtract(min, chart.yAxisPadding());
            });
            return chart;
        }

        // create global charts
        env.winratioChart = dc.pieChart("#chart-winratio");
        env.crawlChart = dc.pieChart("#chart-crawl");
        env.lineChart = nonzero_min(dc.lineChart("#chart-timeline"));
        env.dateRangeChart = nonzero_min(dc.barChart('#chart-date-range'));

        env.dayOfWeekChart = dc.rowChart("#chart-dayofweek");
        env.dataTable = dc.dataTable('#data-table');

        var model = model_.map(function(val, idx, arr) {
            val.date = moment(val.date);
            return val;
        });
        // FIXME: might be better to do this in backend
        model = model.sort(function(a, b) {
            return a.date - b.date;
        });
        var score = 1200;
        for (i = 0; i < model.length; i++) {
            score += model[i].points;
            model[i].score = score;
        }
        env.ndx = crossfilter(model);
        var all = env.ndx.groupAll();

        var dateDim = env.ndx.dimension(d => d.date);
        var dateGroup = dateDim.group();

        var dayOfWeek = env.ndx.dimension(function(d) {
            var day = d.date.day();
            var name = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            return day + '.' + name[day];
        });
        var dayOfWeekGroup = dayOfWeek.group();

        var dayFirst = dateDim.bottom(1)[0].date;
        var dayLast = dateDim.top(1)[0].date;

        var scoreGroup = dateDim.group().reduce(
            function(p, v, nf) {
                // add
                return Math.max(p, v.score);
            },
            function(p, v, nf) {
                // remove
                // FIXME
                return Math.max(p, v.score);
            },
            function() {
                // initial
                return 0;
            });
        env.lineChart
            .rangeChart(env.dateRangeChart)
            .dimension(dateDim)
            .group(scoreGroup)
            .renderArea(true)
            .height(200)
            .renderHorizontalGridLines(true)
            .brushOn(false)
            .x(d3.time.scale().domain([dayFirst, dayLast]))
            .xUnits(d3.time.days)
            .elasticY(true)
            .yAxisPadding(50)
            .xAxisPadding(50)
            .yAxisLabel("", 10)
            .renderDataPoints(true)
            //.legend(dc.legend())
            // .controlsUseVisibility(true)
            .title(function(d) {
                return moment(d.key).format("ddd, MMMM Do YYYY") + ": " + d.value;
            });

        env.dateRangeChart
            .height(75)
            .elasticY(true)
            .dimension(dateDim)
            .group(scoreGroup)
            .centerBar(false)
            .gap(1)
            .x(d3.time.scale().domain([dayFirst, dayLast]))
            .round(d3.time.week.round)
            .xUnits(d3.time.weeks)
            .alwaysUseRounding(true)
            .controlsUseVisibility(true)
            .yAxis().ticks(0);

        var wonDim = env.ndx.dimension(d => d.won);
        var wonGroup = wonDim.group();

        var crawlDim = env.ndx.dimension(d => d.crawl);
        var crawlGroup = crawlDim.group();

        env.winratioChart
            .colors(d3.scale.ordinal()
                .domain([true, false])
                .range(['#1f77b4', '#d62728']))
            .label(function(d) {
                if (env.winratioChart.hasFilter() && !env.winratioChart.hasFilter(d.key)) {
                    return '(0%)';
                }
                return Math.floor(d.value / all.value() * 100) + "%";
            })
            .width(300)
            .height(140)
            .innerRadius(25)
            .cx(70).cy(70)
            .externalRadiusPadding(10)
            .dimension(wonDim)
            .group(wonGroup)
            .controlsUseVisibility(true)
            .legend(dc.legend().x(150).y(20).itemHeight(13).gap(2));

        env.crawlChart
            .colors(d3.scale.ordinal()
                .domain([true, false])
                .range(['#1f77b4', '#d62728']))
            .label(function(d) {
                if (env.crawlChart.hasFilter() && !env.crawlChart.hasFilter(d.key)) {
                    return '(0%)';
                }
                return Math.floor(d.value / all.value() * 100) + "%";
            })
        .width(300)
            .height(140)
            .innerRadius(25)
            .cx(70).cy(70)
            .externalRadiusPadding(10)
            .dimension(crawlDim)
            .group(crawlGroup)
            .controlsUseVisibility(true)
            .legend(dc.legend().x(150).y(20).itemHeight(13).gap(2));

        env.dayOfWeekChart
            .width(300)
            .height(140)
            .group(dayOfWeekGroup)
            .dimension(dayOfWeek)
            .ordinalColors(['#3182bd', '#3182bd', '#3182bd', '#3182bd', '#3182bd'])
            .elasticX(true)
            .label(function(d) {
                return d.key.split('.')[1];
            })
            .title(function(d) {
                return d.value;
            })
            .xAxis().ticks(4);


        env.dataTable
            .dimension(dateDim)
            .group(function(d) {
                return d.date;
            })
            .columns([
                {
                    label: 'Date',
                    format: function(d) {
                        return d.date.format('ll');
                    }
                },
                'team',
                'points',
                'score',
            ])
            .showGroups(false)
            .sortBy(d => d.date)
            .order(d3.descending);

        dc.renderAll();
    });
}
