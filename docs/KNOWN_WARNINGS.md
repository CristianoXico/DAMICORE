# Known Warnings and Dependencies

## External Dependencies Warnings

### numpy.row_stack DeprecationWarning
- **Source**: toyplot package
- **Description**: Warning about deprecated `row_stack` alias, suggesting to use `np.vstack` directly
- **Location**: toyplot.coordinates.Axis._finalize()
- **Impact**: Aesthetic only, does not affect functionality
- **Resolution**: Cannot be fixed locally as it's in external dependency code
- **Recommendation**: Monitor toyplot package updates for future fixes

### matplotlib/phylo UserWarning
- **Source**: Biopython package
- **Description**: Warning about non-interactive FigureCanvasAgg
- **Location**: Biopython/phylo visualization code
- **Impact**: Aesthetic only, does not affect functionality
- **Resolution**: Cannot be fixed locally as it's in external dependency code
- **Recommendation**: Monitor Biopython package updates for future fixes

## Recommendations
1. These warnings do not affect core functionality and can be safely ignored
2. Keep dependencies up to date for potential future fixes
3. If these warnings become problematic, consider:
   - Opening issues upstream in toyplot and Biopython repositories
   - Exploring alternative visualization libraries if necessary
   - Using warnings filter to suppress these specific warnings if they become too distracting
