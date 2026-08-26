# Changelog

All notable changes to this project will be documented in this file.

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
