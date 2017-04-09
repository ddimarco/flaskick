var setupCharts = function(playerid) {
    $.get('/api/playermatches/' + playerid, function(model_) {
        // create global charts
        env.winratioChart = dc.pieChart("#chart-winratio");
        env.crawlChart = dc.pieChart("#chart-crawl");
        env.dateRangeChart = dc.barChart('#chart-date-range');
        env.lineChart = dc.lineChart("#chart-timeline");

        var model = model_.map(function(val, idx, arr) {
            val.date = moment(val.date);
            return val;
        });


        // crossfilter
        env.ndx = crossfilter(model.sort(function(a, b) {
            return a.date - b.date;
        }));

        var timeDim = env.ndx.dimension(d => d.date);
        var timeGroup = timeDim.group();
        var dayFirst = timeDim.bottom(1)[0].date;
        var dayLast = timeDim.top(1)[0].date;


        var wonDim = env.ndx.dimension(d => d.won);
        var wonGroup = wonDim.group();

        var crawlDim = env.ndx.dimension(d => d.crawl);
        var crawlGroup = crawlDim.group();

        //var pointsGroup = timeDim.group().reduceSum( d => d.points);
        var pointsGroup = timeDim.group().reduce(
            function(p, v) {
                return p + v.points;
            },
            function(p, v) {
                return p - v.points;
            },
            function() {
                return 0;
            });

        env.winratioChart
            .colors(d3.scale.ordinal()
                .domain([true, false])
                .range(['#1f77b4', '#d62728']))

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

        .width(300)
            .height(140)
            .innerRadius(25)
            .cx(70).cy(70)
            .externalRadiusPadding(10)
            .dimension(crawlDim)
            .group(crawlGroup)
            .controlsUseVisibility(true)
            .legend(dc.legend().x(150).y(20).itemHeight(13).gap(2));

        env.dateRangeChart
            .width(400)
            .height(50)
            .margins({
                top: 0,
                right: 10,
                bottom: 20,
                left: 30
            })
            .dimension(timeDim)
            .group(timeGroup)
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
            .width(400)
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
            .rangeChart(env.dateRangeChart)
            .dimension(timeDim)
            // .group(timeGroup)
            .group(pointsGroup)
            .valueAccessor(d => {
                return d.value;
            })
            //.legend(dc.legend())
            .controlsUseVisibility(true)
            .title(function(d) {
                return moment(d.key).format("ddd, MMMM Do YYYY") + ": " + d.value;
            });



        dc.renderAll();
    });
}
