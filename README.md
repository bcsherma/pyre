# PYRE: Python retrosheet event file parser

Pyre is a library for parsing retrosheet event files to generate tabular data.
Pyre also downloads and manages all retrosheet data for you so you don't have
to sort out what you do and don't have in the appropriate directory to generate
tabular data from event files.

## Event File Fields:

| Implemented        | Index | Meaning                                     | Header                    |
| ------------------ | ----- | ------------------------------------------- | ------------------------- |
| :heavy_check_mark: | 0     | Game ID                                     | GAME_ID                   |
| :heavy_check_mark: | 1     | Visiting team                               | AWAY_TEAM_ID              |
| :heavy_check_mark: | 2     | Inning                                      | INN_CT                    |
| :heavy_check_mark: | 3     | Batting team                                | BAT_HOME_ID               |
| :heavy_check_mark: | 4     | Outs                                        | OUTS_CT                   |
| :heavy_check_mark: | 5     | Balls                                       | BALLS_CT                  |
| :heavy_check_mark: | 8     | Visitor score                               | AWAY_SCORE_CT             |
| :heavy_check_mark: | 9     | Home score                                  | HOME_SCORE_CT             |
| :heavy_check_mark: | 10    | Batter                                      | BAT_ID                    |
| :heavy_check_mark: | 11    | Batter hand                                 | BAT_HAND_CD               |
| :heavy_check_mark: | 12    | Result batter                               | RESP_BAT_ID               |
| :heavy_check_mark: | 13    | Result batter hand                          | RESP_BAT_HAND_CD          |
| :heavy_check_mark: | 14    | Pitcher                                     | PIT_ID                    |
| :heavy_check_mark: | 15    | Pitcher hand                                | PIT_HAND_CD               |
|                    | 16    | Result pitcher                              | RESP_PIT_ID               |
|                    | 17    | Result pitcher hand                         | RESP_PIT_HAND_CD          |
| :heavy_check_mark: | 18    | Catcher                                     | POS2_FLD_ID               |
| :heavy_check_mark: | 19    | First baseman                               | POS3_FLD_ID               |
| :heavy_check_mark: | 20    | Second baseman                              | POS4_FLD_ID               |
| :heavy_check_mark: | 21    | Third baseman                               | POS5_FLD_ID               |
| :heavy_check_mark: | 22    | Shortstop                                   | POS6_FLD_ID               |
| :heavy_check_mark: | 23    | Left fielder                                | POS7_FLD_ID               |
| :heavy_check_mark: | 24    | Center fielder                              | POS8_FLD_ID               |
| :heavy_check_mark: | 25    | Right fielder                               | POS9_FLD_ID               |
| :heavy_check_mark: | 26    | Runner on first                             | BASE1_RUN_ID              |
| :heavy_check_mark: | 27    | Runner on second                            | BASE2_RUN_ID              |
| :heavy_check_mark: | 28    | Runner on third                             | BASE3_RUN_ID              |
| :heavy_check_mark: | 29    | Event text                                  | EVENT_TX                  |
|                    | 30    | Leadoff flag                                | LEADOFF_FL                |
|                    | 31    | Pinch-hit flag                              | PH_FL                     |
|                    | 32    | Defensive position                          | BAT_FLD_CD                |
|                    | 33    | Lineup position                             | BAT_LINEUP_ID             |
|                    | 34    | Event type                                  | EVENT_CD                  |
|                    | 35    | Batter event flag                           | BAT_EVENT_FL              |
|                    | 36    | Official time at bat flag                   | AB_FL                     |
| :heavy_check_mark: | 37    | Hit value                                   | H_CD                      |
|                    | 38    | Sacrifice hit flag                          | SH_FL                     |
| :heavy_check_mark: | 39    | Sacrifice fly flag                          | SF_FL                     |
|                    | 40    | Outs on play                                | EVENT_OUTS_CT             |
| :heavy_check_mark: | 41    | Double play flag                            | DP_FL                     |
| :heavy_check_mark: | 42    | Triple play flag                            | TP_FL                     |
|                    | 43    | RBI on play                                 | RBI_CT                    |
| :heavy_check_mark: | 44    | Wild pitch flag                             | WP_FL                     |
| :heavy_check_mark: | 45    | Passed ball flag                            | PB_FL                     |
|                    | 46    | Fielded by                                  | FLD_CD                    |
| :heavy_check_mark: | 47    | Batted ball type                            | BATTEDBALL_CD             |
| :heavy_check_mark: | 48    | Bunt flag                                   | BUNT_FL                   |
| :heavy_check_mark: | 49    | Foul flag                                   | FOUL_FL                   |
|                    | 50    | Hit location                                | BATTEDBALL_LOC_TX         |
| :heavy_check_mark: | 51    | Number of errors                            | ERR_CT                    |
| :heavy_check_mark: | 52    | 1st error player                            | ERR1_FLD_CD               |
|                    | 53    | 1st error type                              | ERR1_CD                   |
| :heavy_check_mark: | 54    | 2nd error player                            | ERR2_FLD_CD               |
|                    | 55    | 2nd error type                              | ERR2_CD                   |
| :heavy_check_mark: | 56    | 3rd error player                            | ERR3_FLD_CD               |
|                    | 57    | 3rd error type                              | ERR3_CD                   |
| :heavy_check_mark: | 58    | Batter destination                          | BAT_DEST_ID               |
| :heavy_check_mark: | 59    | Runner on first destination                 | RUN1_DEST_ID              |
| :heavy_check_mark: | 60    | Runner on second destination                | RUN2_DEST_ID              |
| :heavy_check_mark: | 61    | Runner on third destination                 | RUN3_DEST_ID              |
|                    | 62    | Play on batter                              | BAT_PLAY_TX               |
|                    | 63    | Play on runner on first                     | RUN1_PLAY_TX              |
|                    | 64    | Play on runner on second                    | RUN2_PLAY_TX              |
|                    | 65    | Play on runner on third                     | RUN3_PLAY_TX              |
|                    | 66    | Stolen base for runner on first             | RUN1_SB_FL                |
|                    | 67    | Stolen base for runner on second            | RUN2_SB_FL                |
|                    | 68    | Stolen base for runner on third             | RUN3_SB_FL                |
|                    | 69    | Caught stealing for runner on first         | RUN1_CS_FL                |
|                    | 70    | Caught stealing for runner on second        | RUN2_CS_FL                |
|                    | 71    | Caught stealing for runner on third         | RUN3_CS_FL                |
|                    | 72    | Pickoff of runner on first                  | RUN1_PK_FL                |
|                    | 73    | Pickoff of runner on second                 | RUN2_PK_FL                |
|                    | 74    | Pickoff of runner on third                  | RUN3_PK_FL                |
|                    | 75    | Pitcher charged with runner on first        | RUN1_RESP_PIT_ID          |
|                    | 76    | Pitcher charged with runner on second       | RUN2_RESP_PIT_ID          |
|                    | 77    | Pitcher charged with runner on third        | RUN3_RESP_PIT_ID          |
|                    | 78    | New game flag                               | GAME_NEW_FL               |
|                    | 79    | End game flag                               | GAME_END_FL               |
|                    | 80    | Pinch-runner on first                       | PR_RUN1_FL                |
|                    | 81    | Pinch-runner on second                      | PR_RUN2_FL                |
|                    | 82    | Pinch-runner on third                       | PR_RUN3_FL                |
|                    | 83    | Runner removed for pinch-runner on first    | REMOVED_FOR_PR_RUN1_ID    |
|                    | 84    | Runner removed for pinch-runner on second   | REMOVED_FOR_PR_RUN2_ID    |
|                    | 85    | Runner removed for pinch-runner on third    | REMOVED_FOR_PR_RUN3_ID    |
|                    | 86    | Batter removed for pinch-hitter             | REMOVED_FOR_PH_BAT_ID     |
|                    | 87    | Position of batter removed for pinch-hitter | REMOVED_FOR_PH_BAT_FLD_CD |
|                    | 88    | Fielder with first putout                   | PO1_FLD_CD                |
|                    | 89    | Fielder with second putout                  | PO2_FLD_CD                |
|                    | 90    | Fielder with third putout                   | PO3_FLD_CD                |
|                    | 91    | Fielder with first assist                   | ASS1_FLD_CD               |
|                    | 92    | Fielder with second assist                  | ASS2_FLD_CD               |
|                    | 93    | Fielder with third assist                   | ASS3_FLD_CD               |
|                    | 94    | Fielder with fourth assist                  | ASS4_FLD_CD               |
|                    | 95    | Fielder with fifth assist                   | ASS5_FLD_CD               |
|                    | 96    | Event number                                | EVENT_ID                  |
