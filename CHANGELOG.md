# Changelog

All notable changes to this project will be documented in this file.

## [0.8.3] - 2026-08-31
## Changed
-  Removed print_statements from plot_fight_graph(fighter_link, degree, notebook=False)
-  Removed print statements from get_data()

## [0.8.2] - 2026-08-27
## Changed
-  Changed `plot_body` to download fonts from github

## [0.8.1] - 2026-08-27
## Changed
-  Changed comments

## [0.8.0] - 2026-08-27
## Removed
-  `plot_cv(cv_labels, cv_accuracies, title="Cross Validation Accuracy")` removed
-  `plot_test(accuracy, title="Test Accuracy")` removed
### Added
-  `plot_fight_graph(fighter_link, degree)` added
-  `plot_body(minimum, maximum, title, head, body, leg, head_label, body_label, leg_label, suffix)` added
-  `plot_line_graph(title, x_label, x_values, y_label, y_values, average=True)` added
-  `plot_bar_graph(title, x_label, x_values, y_label, y_values, average=True)` added

## [0.7.4] - 2026-08-27
## Changed
-  `get_fighter_history(fighter_link)` refactored to remove parameters
-  `get_fighter_statistic(fighter_link)` refactored to remove parameters
-  
## [0.7.3] - 2026-08-26
## Changed
-  `search(data, column, query, matches)` refactored
-  `get_elo(r, k, s)` refactored to remove parameters

## [0.7.2] - 2026-08-26
## Changed
-  `convert_odds(odds)` refactored to remove parameter

## [0.7.1] - 2026-08-13
### Fixed
-  `get_fighter_statistic(fighter_link, fighter_bio, fights_df, rounds_df, r=1500, k=30, s=400)` fixed

## [0.7.0] - 2026-08-13
### Added
- `plot_cv(cv_labels, cv_accuracies, title="Cross Validation Accuracy")` added 
- `plot_test(accuracy, title="Test Accuracy")` added 

## [0.6.0] - 2026-08-12
### Added
- `convert_odds(odds, probability)` added 
- `train_test_split(fights_df, test_size=0.2)` added 

## [0.5.0] - 2026-08-11
### Added
- `convert_odds(odds, probability)` added 
- `convert_gender(gender)` added 
- `convert_weight(weight)` added
- `mirror(df, cols_1, cols_2, in_order)` added

## [0.4.1] - 2026-08-11
### Added
- `get_fighter_statistic(fighter_link, fighter_bio, fights_df, rounds_df, r=1500, k=30, s=400)` added

## [0.4.0] - 2026-08-11
### Added
- `get_fighter_statistic(fighter_link, fighter_bio, fights_df, rounds_df, r=1500, k=30, s=400)` for obtaining past fight data for an individual fighter

## [0.3.0] - 2026-08-11
### Added
- `get_fighter_history(fighter_link, fighter_bio , fights_df)` for obtaining past fight data for an individual fighter

## [0.2.0] - 2026-08-11
### Added
- `get_elo(fight_df, fighter_df, r=1500, k=30, s=400)` for obtaining Elo data

## [0.1.1] - 2026-08-10

### Added
- Minor changes to printing of `get_data()`

## [0.1.0] - 2026-08-10

### Added

- Initial release
- `get_data()` for obtaining UFC data
