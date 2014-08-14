function detector_data = htmProcessMeasurements(root)

    % Initialise the output as an empty struct
    detector_data = struct();
    
    % And loop over all children of the root element in the hope that they
    % all are gantry nodes ...
    for g = 1:length(root.Children)
        % Children of the <root msg="long_status"> are <gantry> nodes
        gantry_node = root.Children(g);
        if strcmp ( gantry_node.Name, 'gantry' )
            gantry_field_name = gantry_node.Attrib.id;
            gantry_field_name = strrep(gantry_field_name, '-', '_');
            gantry_field_name = strrep(gantry_field_name, ' ', '_');
            for i = 1:length(gantry_node.Children)
                device_node = gantry_node.Children(i);
                if strcmp ( device_node.Name, 'device' )
                    device_id = str2double(device_node.Attrib.id);
                    % Only device id 20 is interesting (detector data)
                    if device_id ~= 20
                        continue
                    end
                    % Cell vector for directions
                    gantry_detectors = cell(2,1);
                    for j = 1:length(device_node.Children)
                        subdevice_node = device_node.Children(j);
                        if strcmp ( subdevice_node.Name, 'subdevice' )
                            dir_idx = str2double(subdevice_node.Attrib.id)+1;
                            % Allocate space for up to 3 lanes
                            lanes = cell(3,1);
                            for k = 1:length(subdevice_node.Children)
                                lane_node = subdevice_node.Children(k);
                                if strcmp ( lane_node.Name, 'lane' )
                                    % Lane ID goes from 0 (leftmost, the fastest lane)
                                    % to 1 or 2 (rightmost, the slowest lane). The index
                                    % has to start with 1, we will have therefore
                                    % indices 1,2 or 1,2,3.
                                    lane_idx = str2double(lane_node.Attrib.id)+1;
                                    % Create 9 categories x 3
                                    categories = ones(9,3)*NaN;
                                    for n = 1:length(lane_node.Children)
                                        category_node = lane_node.Children(n);
                                        if strcmp ( category_node.Name, 'category' )
                                            cat_idx = str2double(category_node.Attrib.id)+1;
                                            for m = 1:length(category_node.Children)
                                                measurement_node = category_node.Children(m);
                                                if ~isempty(measurement_node.Children)
                                                    measurement_val = str2double(measurement_node.Children(1).Data);
                                                    if strcmp ( measurement_node.Name, 'intensity' )
                                                        categories(cat_idx,1) = measurement_val;
                                                    elseif strcmp ( measurement_node.Name, 'occupancy' )
                                                        categories(cat_idx,2) = measurement_val;
                                                    elseif strcmp ( measurement_node.Name, 'speed' )
                                                        categories(cat_idx,3) = measurement_val;
                                                    end
                                                end
                                            end
                                        end
                                    end
                                    % Now we have the measurements by vehicle-type
                                    % and we shall assign the matrix to the
                                    % appropriate gantry/detector
                                    lanes{lane_idx} = categories;
                                end
                            end
                            % We have processed all lanes of the given sub-device
                            gantry_detectors{dir_idx} = lanes;
                        end
                    end
                end
            end
            % We have processed all tags of the gantry node, let's store
            % the data
            detector_data.(gantry_field_name) = gantry_detectors;
        end
    end
end