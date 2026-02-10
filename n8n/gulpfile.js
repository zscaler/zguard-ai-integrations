const gulp = require('gulp');

function buildIcons() {
  return gulp.src('nodes/**/*.svg')
    .pipe(gulp.dest('dist/nodes'));
}

exports['build:icons'] = buildIcons;
exports.default = buildIcons;
