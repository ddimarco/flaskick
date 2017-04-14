var setupCharts = function(playerid) {
    $.get('/api/playermatches/' + playerid, function(model_) {
        // create global charts
        env.winratioChart = dc.pieChart("#chart-winratio");
        env.crawlChart = dc.pieChart("#chart-crawl");
        env.dateRangeChart = dc.barChart('#chart-date-range');
        env.lineChart = dc.lineChart("#chart-timeline");

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
        // console.log(model);
        env.ndx = crossfilter(model);
        var all = env.ndx.groupAll();

        var timeDim = env.ndx.dimension(d => d.date);
        var timeGroup = timeDim.group();

        var dayOfWeek = env.ndx.dimension(function(d) {
            var day = d.date.day();
            var name = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            return day + '.' + name[day];
        });
        var dayOfWeekGroup = dayOfWeek.group();

        var dayFirst = timeDim.bottom(1)[0].date;
        var dayLast = timeDim.top(1)[0].date;

        var scoreDim = env.ndx.dimension(d => d.score);
        var scoreGroup = scoreDim.group().reduceSum(d => d.score);

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
            .label(function(d) {
                return d.key.split('.')[1];
            })
            .title(function(d) {
                return d.value;
            });
            // .xAxis().ticks(4);

        env.dateRangeChart
            .width(400)
            .height(50)
            .margins({
                top: 0,
                right: 10,
                bottom: 20,
                left: 30
            })
            .dimension(scoreDim)
            .group(scoreGroup)
            .centerBar(false)
            .gap(1)
            .x(d3.time.scale().domain([dayFirst, dayLast]))
            .round(d3.time.week.round)
            .xUnits(d3.time.weeks)
            .alwaysUseRounding(true)
            .controlsUseVisibility(true)
            .yAxis().ticks(0);



        env.lineChart
            .renderArea(true)
            // .width(400)
            .height(200)
            .margins({
                top: 20,
                right: 10,
                bottom: 20,
                left: 30
            })
            .clipPadding(5)
            //.colors(d3.scale.ordinal().range(['#1f77b4', '#d62728']))
            .renderHorizontalGridLines(true)
            .elasticY(true)
            .brushOn(false)
            .x(d3.time.scale().domain([dayFirst, dayLast]))
            .round(d3.time.days.round)
            .xUnits(d3.time.days)
            // .rangeChart(env.dateRangeChart)
            .dimension(timeDim)
            .group(scoreGroup)
            // .valueAccessor(d => {
            //     return d.value;
            // })
            //.legend(dc.legend())
            .controlsUseVisibility(true)
            .title(function(d) {
                return moment(d.key).format("ddd, MMMM Do YYYY") + ": " + d.value;
            });

        env.dataTable
            .dimension(timeDim)
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
            .sortBy(d => d.date)
            .order(d3.descending);




        dc.renderAll();
    });
}
