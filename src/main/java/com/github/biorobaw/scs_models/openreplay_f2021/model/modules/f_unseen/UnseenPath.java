package com.github.biorobaw.scs_models.openreplay_f2021.model.modules.f_unseen;

import com.github.biorobaw.scs.experiment.Experiment;

import java.io.*;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Scanner;

public class UnseenPath {
    public ArrayList<Integer> path1 = new ArrayList<Integer>();
    public ArrayList<Integer> path2 = new ArrayList<Integer>();
    public UnseenPath(String file_of_paths) {

        try (Scanner scanner = new Scanner(new File(file_of_paths));) {
            String line;
            int path_counter = 0;
            while (scanner.hasNextLine()) {
                String[] values = scanner.nextLine().split(",");
                if(path_counter ==0){
                    for(String val : values){
                        this.path1.add(Integer.parseInt(val));
                    }
                }
                else if (path_counter ==1){
                    for(String val : values){
                        this.path2.add(Integer.parseInt(val));
                    }
                }
                path_counter ++;
            }
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
