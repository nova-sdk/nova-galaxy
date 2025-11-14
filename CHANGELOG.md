## Nova Galaxy 0.12.0 (in progress)

### Nova Galaxy 0.11.5
- Fixes a packaging issue where some dependencies weren't included in the final build (thanks to John Duggan). Pull request TODO

### Nova Galaxy 0.11.4
- Allows connecting to a Galaxy URL that returns a redirect (thanks to John Duggan). [Pull request 57](https://github.com/nova-model/nova-galaxy/pull/57)

### Nova Galaxy 0.11.3
- Minor fixes for workflow parameters (thanks to Andrew Ayres). [Pull request 53](https://github.com/nova-model/nova-galaxy/pull/53)

### Nova Galaxy 0.11.2
- Workflow parameters are now more explicitly defined (thanks to Andrew Ayres). [Commit](https://github.com/nova-model/nova-galaxy/commit/fc7ca763c400698e51f81c99764bb8c696b6ecca)

### Nova Galaxy 0.11.1
- Improved the performance of Job.get_url when check_url parameter is set to False (thanks to John Duggan). [Pull request 43](https://github.com/nova-model/nova-galaxy/pull/43)

### Nova Galaxy 0.11.0
- Added detailed job status (thanks to Sergey Yakubov) [Pull request 40](https://github.com/nova-model/nova-galaxy/pull/40)
- Added ability to mark datasets as remote files, and Nova-Galaxy will attempt to ingress them when running tools (thanks to Gregory Cage). [Merge Request 25](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/25)
- Added ability to mark datasets as remote files, and Nova-Galaxy will attempt to ingress them when running tools (thanks to Gregory Cage). [Merge Request 25](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/25)
- Datasets can now be linked to existing datasets when uploaded as tool parameters using force_upload parameter. This saves users from having to upload a dataset multiple times if not necessary (thanks to Gregory Cage). [Merge Request 25](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/25)
- Dependency update (thanks to Sergey Yakubov). [Commit](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/commit/1f532dbbd5c6603c7e358101c0b3830fb2b36f5a)

### Nova Galaxy 0.10.0
- Added ToolRunner class to facilitate an event driven running of tools (thanks to Sergey Yakubov). [Merge Request 24](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/24)
- Added `get_full_status` method to tool in order to get detailed messages mostly for error states (thanks to Gregory Cage). [Merge Request 23](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/23)

### Nova Galaxy 0.9.0
- When uploading datasets with manually set content, the upstream name will mirror the local name property of the dataset (thanks to Gregory Cage). [Merge Request 22](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/22)
- New WorkStates for the actual process of stopping and canceling jobs (separate from the terminal states already present) (thanks to Sergey Yakubov and Gregory Cage). [Merge Request 22](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/22)
- Fixed major bug where tools were not being stopped and fetching results properly (canceling worked fine) (thanks to Gregory Cage). [Merge Request 22](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/22)
- Made tool status thread safe (thanks to Sergey Yakubov and Gregory Cage). [Merge Request 22](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/22)
- If canceling or stopping jobs in the uploading data state, will stop the uploading when able (thanks to Sergey Yakubov and Gregory Cage). [Merge Request 22](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/22)
- Misc backend code cleanup (thanks to Sergey Yakubov and Gregory Cage). [Merge Request 22](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/22)
- Now returns file type automatically if available (thanks to Gregory Cage). [Merge Request 21](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/21)
- Returns file content as bytes instead of string (thanks to Gregory Cage). [Merge Request 21](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/21)
- Can now fetch specific stdout and stderr positions and length (thanks to Gregory Cage). [Merge Request 19](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/19)

### Nova Galaxy, 0.8.0
- `get_data_store()` has been added to the ConnectionHelper class. This functionally does the same thing as create_data_store, but users can choose whether to only use existing upstream data stores. `create_data_store` creates data stores by default and connects to existing ones as well automatically (thanks to Gregory Cage).  [Merge Request 18](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/18)
- `Connections.connect()` can now be used with or without the `with` keyword. Consequently, stores can also be created outside a `with` block. `Connection.close()` performs the clean up that exiting the `with` block provides (thanks to Gregory Cage). [Merge Request 18](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/18)
- Data stores can be cleaned up manually (thanks to Gregory Cage). [Merge Request 18](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/18)
- Can now wait for the result of a running tool (thanks to Gregory Cage). [Merge Request 18](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/18)
- Allow users to choose to check URL when calling get_url() from a Tool (thanks to Gregory Cage). [Merge Request 17](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/17)
- Return more detailed information when getting the content of a DatasetCollection (thanks to Gregory Cage). [Merge Request 17](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/17)
- Data stores are now persisted by default. A new mark_for_cleanup method has been provided to clean up data stores after usage. The persist method's behavior remains unchanged (thanks to Gregory Cage). [Merge Request 17](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/17)
- Allow Dataset content to be set manually in memory rather than only loading from a file or downloading from Galaxy (thanks to Gregory Cage). [Merge Request 16](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/16)
- Add file type (extensions) to Datasets (thanks to Gregory Cage). [Merge Request 16](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/16)
- Add more states to Work State enum (thanks to Gregory Cage). [Merge Request 15](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/15)
- Speeds ups recovering tools from data stores. (thanks to Gregory Cage). [Merge Request 14](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/14)

### Nova Galaxy, 0.7.0
- Reworks some issues where the url was trying to be fetched in scenarios where it would take the full timeout (thanks to Gregory Cage).  [Merge Request 13](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/13)
- Added a lot more user documentation (thanks to Gregory Cage).  [Merge Request 13](https://code.ornl.gov/ndip/public-packages/nova-galaxy/-/merge_requests/13)
- Changed the Workstate enum to have string values (much more useful when trying to serialize the value) (thanks to Gregory Cage).  [Merge Request 13](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/13)
- Changes Nova class name to Connection, and NovaConnection to ConnectionHelper (thanks to Gregory Cage).  [Merge Request 13](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/13)
- Fix dictionary bug with data stores (thanks to Gregory Cage). [Merge Request 12](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/12)

### Nova Galaxy, 0.6.0
- Add recovery for data stores (thanks to Gregory Cage). [Merge Request 10](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/10)
- Add IDs to tools (thanks to Gregory Cage). [Merge Request 10](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/10)
- Reworked back end infrastructure for managing tool execution. (thanks to Gregory Cage). [Merge Request 8](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/8)
- Add readthedocs support (thanks to Andrew Ayres). [Merge Request 5](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/5)
- Add initial testing for library (thanks to Gregory Cage). [Merge Request 3](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/3)
- Set up read the docs for package (thanks to Andrew Ayres). [Merge Request 4](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/4)
- Add interactive tool execution (thanks to Gregory Cage). [Merge Request 2](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/2)
- Initial implementation of nova library (thanks to Gregory Cage). [Merge Request 1](https://code.ornl.gov/ndip/public-packages/ndip-galaxy/-/merge_requests/1)
