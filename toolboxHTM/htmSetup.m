function htmSetup ( entrancePath, entranceSectionVec, headway, sectionStatsPath, globalStatsPath, statsSectionMat, prefix )
% R=HTMSETUP(E,EV,H,S,G,SM) sets parameters of the HTM interface.
%
% Parameters:
%   entrancePath ......... CSV file containing entrance data
%   entranceSectionVec ... vector of entrance section identifiers; the
%                          order of elements corresponds to the order of
%                          elements in `entrancePath` CSV file
%   headway .............. id of vehicle headway computation method
%   sectionStatsPath .....
%   globalStatsPath ......
%   statsSectionMat ...... matrix of section identifiers, where rows
%                          compose a single arm of an intersection; invalid
%                          values are filled with `NaN`s
%
% This code is part of SIRID project financed by the Technology Agency of
% the Czech Republic under project no. TA02030522
%
% (c) 2014 ÈVUT FD 
%
% Author: Jan Pøikryl <prikryl@fd.cvut.cz>
%
% Version: $Id$

global HTM_PREFIX;

    % Preprocess `statsSectionMat` to sorted vector of section identifiers
    statIds = htmGetSectionStatsIds ( statsSectionMat );
    
    % Update the global prefix of debugging outputs
    HTM_PREFIX = prefix;
        
% ----- END ( htmSetup ) -----