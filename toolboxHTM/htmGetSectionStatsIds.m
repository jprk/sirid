function ids=vgsGetSectionStatsIds ( statsSectionMat )
% I=VGSGETSECTIONSTATSIDS(S) transforms S to sorted vector of unique section identifiers.
%
% Parameters:
% statsSectionMat ... aggregation matrix of section identifiers, where rows
%                     compose a single arm of an intersection; invalid
%                     values are filled with `NaN`s
%
% (c) 2008 ÚTIA AVÈR, v.v.i.
%
% Author: Jan Pøikryl <prikryl@utia.cas.cz>
%
% Version: $Id: vgsGetSectionStatsIds.m 2147 2008-08-04 07:00:43Z prikryl $
%

    % Find valid identifies in the section aggregation matrix
    validIds = find ( ~isnan ( statsSectionMat ));
    
    % And create a sorted vector of unique section identifiers.
    ids = unique ( statsSectionMat ( validIds ));
  
% ----- END ( vgsGetSectionStatsIds ) -----   