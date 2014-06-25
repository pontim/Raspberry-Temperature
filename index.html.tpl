<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>{{ location }}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="">

    <link href="css/bootstrap.min.css" rel="stylesheet">
    <link href="css/bootstrap-responsive.min.css" rel="stylesheet">

    <script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.2/jquery.min.js"></script>
    <script type="text/javascript" src="js/bootstrap.min.js"></script>
    <script type="text/javascript" src="js/highcharts.js"></script>
    <script type="text/javascript">
$(function () {
    $('a[data-toggle="pill"]').on('shown', function (e) {
        $('#hour').highcharts({
            chart: {
                type: 'spline'
            },
            title: {
                text: 'Last Hour'
            },
            subtitle: {
                text: "{{ location }}"
            },
            xAxis: {
                type: 'datetime',
                title: {
                    text: 'Time',
                },
            },
            yAxis: {
                title: {
                    text: 'Temperature'
                },
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                spline: {
                    marker: {
                        enabled: false,
                    },
                },
            },
            series: [{
                name: 'Temperature',
                data: [
                    {% for d in hour_data %}
                    [Date.UTC({{ d.time.year }}, {{ d.time.month|int() - 1 }}, {{ d.time.day }}, {{ d.time.hour }}, {{ d.time.minute }}), {{ d.temperature }}],
                    {% endfor %}
                ]
            }]
        });
    });
});
$(function () {
    $('a[data-toggle="pill"]').on('shown', function (e) {
        $('#day').highcharts({
            chart: {
                type: 'spline'
            },
            title: {
                text: 'Last Day'
            },
            subtitle: {
                text: "{{ location }}"
            },
            xAxis: {
                type: 'datetime',
                title: {
                    text: 'Time',
                },
            },
            yAxis: {
                title: {
                    text: 'Temperature'
                },
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                spline: {
                    marker: {
                        enabled: false,
                    },
                },
            },
            series: [{
                name: 'Temperature',
                data: [
                    {% for d in day_data %}
                    [Date.UTC({{ d.time.year }}, {{ d.time.month|int() - 1 }}, {{ d.time.day }}, {{ d.time.hour }}, {{ d.time.minute }}), {{ d.temperature }}],
                    {% endfor %}
                ]
            }]
        });
    });
});
$(function () {
    $('a[data-toggle="pill"]').on('shown', function (e) {
        $('#week').highcharts({
            chart: {
                type: 'spline'
            },
            title: {
                text: 'Last Week'
            },
            subtitle: {
                text: "{{ location }}"
            },
            xAxis: {
                type: 'datetime',
                title: {
                    text: 'Time',
                },
            },
            yAxis: {
                title: {
                    text: 'Temperature'
                },
            },
            legend: {
                enabled: false
            },
            plotOptions: {
                spline: {
                    marker: {
                        enabled: false,
                    },
                },
            },
            series: [{
                name: 'Temperature',
                data: [
                    {% for d in week_data %}
                    [Date.UTC({{ d.time.year }}, {{ d.time.month|int() - 1 }}, {{ d.time.day }}, {{ d.time.hour }}, {{ d.time.minute }}), {{ d.temperature }}],
                    {% endfor %}
                ]
            }]
        });
    });
});
    </script>
  </head>

  <body>

    <div class="container">

      <div class="span10 offset1">
        <header class="jumbotron subhead">
          <h1>{{ location }} {{ temperature }} F</h1>
          <p class="lead">{{ time }}</p>
        </header>
      </div>

      <div class="span2 offset1">
        <ul class="nav nav-pills nav-stacked" id="graphtabs">
          <li class=""><a href="#hour" data-toggle="pill">Hour</a></li>
          <li><a href="#day" data-toggle="pill">Day</a></li>
          <li><a href="#week" data-toggle="pill">Week</a></li>
        </ul>
      </div>

      <div class="span8">
        <div class="tab-content" style="overflow-y:hidden;">
          <div id="hour" class="tab-pane"></div>
          <div class="tab-pane" id="day"></div>
          <div class="tab-pane" id="week"></div>
        </div>
      </div>

    </div>
    <script type="text/javascript">
$(document).ready(function () {
    $('[data-toggle="pill"][href="#hour"]').tab('show');
});
    </script>
  </body>
</html>
